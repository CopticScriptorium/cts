import logging
import re
from django import forms
from django.http import Http404
from django.urls import reverse
from django.db.models import Case, F, IntegerField, Q, When
from django.shortcuts import get_object_or_404, redirect, render
from django.db.models.functions import Lower
from texts.search_fields import SearchField
from texts.ft_search import Search
from django.views.decorators.cache import cache_page
from django.core.cache import cache
from django.conf import settings
import texts.models as models
import texts.urn
import base64

from django.template.defaulttags import register

HTML_TAG_REGEX = re.compile(r"<[^>]*?>")

logger = logging.getLogger(__name__)

@register.filter(name="keyvalue")
def keyvalue(dict, key):
    return dict.get(key)

@cache_page(settings.CACHE_TTL)
def home_view(request):
    "Home"
    context = _base_context()
    context.update({"page_title":"Home"})
    return render(request, "home.html", context)


@cache_page(settings.CACHE_TTL)
def corpus_view(request, corpus=None):
    corpus_object = get_object_or_404(models.Corpus, slug=corpus)

    # This is almost what we need, but because of some ORM quirks (LEFT OUTER JOINs where we needed INNER JOINs)
    # every text with a valid `order` metadatum will appear twice in these results: once with an "order" annotation,
    # and once without.
    texts = (
        models.Text.objects.filter(corpus=corpus_object)
        .annotate(
            order=Case(
                When(text_meta__name="order", then="text_meta__value"),
                output_field=IntegerField(),
            )
        )
        .distinct()
        .order_by("order", "id")
    )

    # to handle this, for every id, take the one with an "order" if it has one, else fall back to the one without order
    ids = {t.id for t in texts}
    results = []
    for tid in ids:
        no_order_match = [t for t in texts if t.id == tid and t.order is None]
        order_match = [t for t in texts if t.id == tid and t.order is not None]
        if len(order_match) == 0:
            # Some corpora, like urn:cts:copticLit:shenoute.those, have only partial orderings--in this case, put the unordered ones last
            no_order_match[0].order = 999999
            results += no_order_match
        else:
            results += order_match
    results = sorted(results, key=lambda t: (t.order, t.id))
    texts = results
    formats = settings.HTML_VISUALISATION_FORMATS
    context = _base_context()
    context.update({"corpus": corpus_object, "texts": texts, "page_title": corpus_object.title, "formats": formats})
    return render(request, "corpus.html", context)


@cache_page(settings.CACHE_TTL)
def text_view(request, corpus=None, text=None, format=None):
    corpus_object = get_object_or_404(models.Corpus, slug=corpus)
    text_object = get_object_or_404(models.Text, corpus=corpus_object.id, slug=text)
    

    if not format:
        visualization = text_object.html_visualizations.all()[0]
        format = visualization.visualization_format["slug"] # Verify this is the correct attribute
        return text_view(request, corpus=corpus, text=text, format=format)
    
    # FIXME: It should probably be `norm` everywhere - will be fixed in data.
    # Changed to use visualization_format_slug
    
    # this is probably wrong?
    visualization = text_object.get_visualization_by_slug(format)
    
    doc_urn = text_object.text_meta.get(name="document_cts_urn").value

    text_object.edition_urn = doc_urn
    text_object.urn_cts_work = texts.urn.cts_work(doc_urn)
    text_object.textgroup_urn = texts.urn.textgroup_urn(doc_urn)
    text_object.corpus_urn = texts.urn.corpus_urn(doc_urn)
    text_object.text_url = "texts/" + text_object.corpus.slug + "/" + text_object.slug

    try:
        next_text_urn = text_object.text_meta.get(name="next").value.strip()
        slug = models.Text.objects.get(
            text_meta__name="document_cts_urn", text_meta__value=next_text_urn
        ).slug
        text_object.next = slug
    except (models.TextMeta.DoesNotExist, models.Text.DoesNotExist):
        logger.error("Next text not found")  # Debug statement
        pass
    try:
        previous_text_urn = text_object.text_meta.get(name="previous").value.strip()
        slug = models.Text.objects.get(
            text_meta__name="document_cts_urn", text_meta__value=previous_text_urn
        ).slug
        text_object.previous = slug
    except (models.TextMeta.DoesNotExist, models.Text.DoesNotExist):
        logger.error("Previous text not found") # Debug statement
        pass
    try:
        text_object.endnote = text_object.text_meta.get(name="endnote").value
    except (models.TextMeta.DoesNotExist, models.Text.DoesNotExist):
        logger.warning("Endnote not found")  # Debug statement
        pass
    visualizations = text_object.html_visualizations.all()
    
    context = _base_context()
    context.update(
        {"text": text_object, "visualization": visualization, "format": format,  "page_title": text_object.title, "visualizations": visualizations}
    )
    return render(request, "text.html", context)


def not_found(request):
    return render(request, "404.html", {})

def _resolve_urn(urn):
    try:
        text = models.Text.objects.get(
            text_meta__name="document_cts_urn", text_meta__value=urn
        )
        return text
    except models.Text.DoesNotExist:
        try:
            corpus = models.Corpus.objects.get(urn_code=urn)
            return corpus
        except models.Corpus.DoesNotExist:
            return None


def urn(request, urn=None):
    # https://github.com/CopticScriptorium/cts/issues/112
    if re.match(r"urn:cts:copticLit:ot.*.crosswire", urn):
        return redirect(
            "https://github.com/CopticScriptorium/corpora/releases/tag/v2.5.0"
        )

    # check to see if the URN is deprecated and redirect if so
    urn = settings.DEPRECATED_URNS.get(urn, urn)
    obj = _resolve_urn(urn)

    if obj.__class__.__name__ == "Text":
        return redirect("text", corpus=obj.corpus.slug, text=obj.slug)
    elif obj.__class__.__name__ == "Corpus":
        return redirect("corpus", corpus=obj.slug)
    return redirect(reverse("search") + f"?text={urn}")

@cache_page(settings.CACHE_TTL)
def index_view(request, special_meta=None):
    context = _base_context()
    try:
        # FIXME hack are the inconsistency in meta names.
        if special_meta=="msName":
            special_meta="ms_name"
        meta = settings.METAS.get(special_meta)
    except KeyError:
        raise Http404(f'Special metadata type "{special_meta}" not found')
    
    value_corpus_pairs = models.Text.get_value_corpus_pairs(meta)

    b64_meta_values = {
        meta_value: str(base64.b64encode(('identity="'+meta_value+'"').encode("ascii")).decode("ascii"))
        for meta_value in value_corpus_pairs.keys()
    }

    b64_corpora = {
        c["annis_corpus_name"]: str(base64.b64encode(c["annis_corpus_name"].encode("ascii")).decode("ascii"))
        for meta_value_list in value_corpus_pairs.values()
        for c in meta_value_list
    }

    all_corpora = {c["annis_corpus_name"] for meta_value_list in value_corpus_pairs.values() for c in meta_value_list}

    annis_corpora = ",".join(list(all_corpora))
    annis_corpora = str(base64.b64encode(annis_corpora.encode("ascii")).decode("ascii"))

    context.update({
        'special_meta': meta["name"] ,
        'value_corpus_pairs': value_corpus_pairs.items,
        'is_corpus': meta["name"] == "corpus",
        'b64_meta_values': b64_meta_values,
        'b64_corpora': b64_corpora,
        'annis_corpora': annis_corpora  
    })
    return render(request, 'index.html', context)


# search --------------------------------------------------------------------------------
def _get_meta_names_for_query_text(text):
    names = [settings.METAS[meta]["name"] for meta in settings.METAS]
    # FIXME: in the original code we are only doing "full text search" 
    # on title, author and urn which explains this code.
    if "title" not in names:
        names.append("title")
    if "author" not in names:
        names.append("author")
    if text.lower().startswith("urn:"):
        names.append("document_cts_urn")
    return names

class SearchForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Get all Meta objects and sort them by name
        # FIXME: Why are we sorting by name? also they are already lowercase.

        special_metas = dict(
            sorted(settings.METAS.items(), key=lambda x: x[1]["name"].lower())
        )
        for sm in special_metas:
            meta_values = models.Text.get_meta_values(special_metas[sm]) # So this is how we actually do "faceting"
            choices = []
            for v in meta_values:
                if special_metas[sm]["name"] == "corpus":
                    try:
                        human_name = models.Corpus.objects.get(
                            annis_corpus_name=v
                        ).title
                    except models.Corpus.DoesNotExist:
                        human_name = v
                else:
                    human_name = v
                human_name = re.sub(HTML_TAG_REGEX, "", human_name)
                choices.append((v, human_name))

            self.fields[special_metas[sm]["name"]] = forms.MultipleChoiceField(
                label=special_metas[sm]["name"],
                required=False,
                choices=choices,
                widget=forms.SelectMultiple(attrs={"class": "search-choice-field"}),
            )

    text = forms.CharField(
        label="query",
        required=False,
        widget=forms.TextInput(attrs={"class": "search-text-field"}),
    )


def _build_queries_for_special_metadata(params):
    queries = []
    for meta_name, meta_values in params.items():
        if meta_name == "text":
            continue
        # The following is probably uneeded because we are already
        # stripping in the import and we can get the values alredy sorted?
        meta_values = sorted([s.strip() for s in meta_values])
        meta_name_query = Q()
        for meta_value in meta_values:
            if meta_value:
                if meta_name == "document_cts_urn":
                    regex = "^" + meta_value.replace(".", r"\.").replace("*", ".*")
                    meta_name_query = meta_name_query | Q(
                        text_meta__name__iexact=meta_name, text_meta__value__regex=regex
                    )
                else:
                    meta_name_query = meta_name_query | Q(
                        text_meta__name__iexact=meta_name,
                        text_meta__value__iexact=meta_value,
                    )
        queries.append(meta_name_query)

    return queries


def _fetch_and_filter_texts_for_special_metadata_query(queries):
    if queries:
        texts = models.Text.objects.all().order_by(Lower("title"))
        for query in queries:
            texts = texts.filter(query)
        add_author_and_urn(texts)
        return texts
    else:
        return models.Text.objects.none()


def _build_explanation(params):
    meta_explanations = []
    for meta_name, meta_values in params.items():
        if meta_name == "text":
            continue
        if meta_name == "corpus":
            new_meta_values = []
            for meta_value in meta_values:
                try:
                    meta_value = models.Corpus.objects.get(
                        annis_corpus_name=meta_value
                    ).title
                except models.Corpus.DoesNotExist:
                    pass
                new_meta_values.append(meta_value)
            meta_values = new_meta_values

        # indicate the special logic used for document_cts_urn
        sep = "=" if meta_name != "document_cts_urn" else "matching"
        meta_name_explanations = [
            f'<span class="meta_pair">{meta_name}</span> {sep} <span class="meta_pair">{meta_value}</span>'
            for meta_value in meta_values
        ]
        meta_explanations.append("(" + " OR ".join(meta_name_explanations) + ")")
    return " AND ".join(meta_explanations)


def _build_result_for_query_text(query_text, texts, explanation):
    results = []
    meta_names = _get_meta_names_for_query_text(query_text)
    for meta_name in meta_names:
        complete_explanation = (
            f'<span class="meta_pair">{query_text}</span> in "{meta_name}"'
        )
        complete_explanation += " with " if explanation else ""
        complete_explanation += explanation

        if meta_name == "document_cts_urn":
            text_results = texts
        else:
            text_results = texts.filter(
                text_meta__name__iexact=meta_name,
                text_meta__value__icontains=query_text,
            )
        add_author_and_urn(text_results)
        results.append({"texts": text_results, "explanation": complete_explanation})
    all_empty_explanation = f'<span class="meta_pair">{query_text}</span> in metadata'
    all_empty_explanation += " with " if explanation else ""
    all_empty_explanation += explanation
    return results, all_empty_explanation


def _base_context():
    context = {
        "search_fields": [
            SearchField("corpus"),
            SearchField("author"),
            SearchField("msName"),
            SearchField("people"),
            SearchField("places"),
            # SearchField("annotation"),
        ],
        "secondary_search_fields": [
            SearchField("translation"),
            SearchField("arabic_translation"),
        ],
    }
    return context


def search(request):
    context = _base_context()

    # possible keys are "text", which is the freetext that a user entered,
    # and slugs corresponding to SpecialMetas (e.g. "author", "translation", ...)
    # which the user can select in the sidebar on right-hand side of the screen
    params = dict(request.GET.lists())
    query_text = params["text"][0] if "text" in params and params["text"] > [''] else None

    # (1) unwrap the list of length 1 in params['text'] if it exists
    # (2) if params['text'] starts with "urn:", treat it as a special case, first checking for redirects, then
    #     copying it to params['document_cts_urn'] (it is in a list to remain symmetric with all other non-'text' fields)
    if query_text:
        urn_redirect = handle_urn(query_text)
        if urn_redirect:
            return urn_redirect

    # returns a list of queries built with Django's Q operator using non-freetext parameters
    queries = _build_queries_for_special_metadata(params)

    # preliminary results--might need to filter more if freetext query is present
    texts = _fetch_and_filter_texts_for_special_metadata_query(queries)
    
    # build base explanation, a string that will be displayed to the user summarizing their search parameters
    explanation = _build_explanation(params)
        
    fulltext_results=[]
    totalHits=0
    search_instance = Search()
    if "text" in params and query_text:
        results, all_empty_explanation = _build_result_for_query_text(
            query_text, texts, explanation
        )
        ft_hits=models.Text.search(query_text)
        if ft_hits["hits"]:
            totalHits=ft_hits["estimatedTotalHits"] #FIXME: either estimatedTotalHits or totalHits (then we need to change the query)
            for result in ft_hits["hits"]:
                logging.info(result["_matchesPosition"])
                # These are the attributes on which we have hits.
                attrs=list(result["_matchesPosition"].keys())
                if "text.normalized" in attrs:
                    hits = {"Normalized text": result["_formatted"]["text"][0]["normalized"]}
                elif "text.normalized_group" in attrs:
                    hits = {"Normalized text group": result["_formatted"]["text"][0]["normalized_group"]}
                elif "text.lemmatized" in attrs:
                    hits = {"Lemmatized": result["_formatted"]["text"][0]["lemmatized"]}
                elif "text.english_translation" in attrs:
                    hits = {"English Translation": result["_formatted"]["text"][0]["english_translation"]}
                else:
                    # Create a simple key value dict for the results
                    hits = {}                    
                    for attr in attrs:
                        if attr.count("slug") == 0:
                        # We are not displaying the slug in the search results
                        # Other than that we respect the settings in the ft_search.py
                        # We need the slug for the url
                            if attr.count(".") > 0:
                                name = attr.split('.')[-1]
                                hits[name] = result["_formatted"]["text_meta"].get(name, '')
                            else:
                                name = attr
                                hits[name] = result["_formatted"].get(name, '')
                logging.info(f'Attribute: {attrs} Hits: {hits}')
                fulltext_results.append({
                    "title": result["_formatted"]["title"],
                    "slug": result["slug"],
                    "corpus_slug": result["corpus_slug"],
                    "hits": hits})
    else:
        results = [{"texts": texts, "explanation": explanation}]
        all_empty_explanation = explanation

    context.update(
        {
            "results": results,
            "totalHits": totalHits,
            "fulltext_results": fulltext_results,
            "form": SearchForm(request.GET),
            "no_query": not any(len(v) for v in request.GET.dict().values()),
            "all_empty": not any(len(r["texts"]) for r in results),
            "all_empty_explanation": all_empty_explanation,
            "query_text": query_text,
        }
    )

    return render(request, "search.html", context)

def _build_remove_query_url(request):
    """Build URL for removing the query text while preserving other parameters."""
    params = request.GET.copy()
    if 'text' in params:
        del params['text']
    # Remove page parameter to reset pagination
    if 'page' in params:
        del params['page']
    return f"?{params.urlencode()}"

def faceted_search(request):
    context = _base_context()
    params = dict(request.GET.lists())
    query_text = params.get("text", [""])[0].strip()
    
    # Get pagination parameters
    page = int(request.GET.get('page', '1'))
    hits_per_page = 20  # You can adjust this number
    
    if query_text and (urn_redirect := handle_urn(query_text)):
        return urn_redirect

    # Build filter query and track active facets
    filters = []
    active_facets = {}
    facet_counts = {}
    remove_facet_urls = {}

    for key, values in params.items():
        if key in ["text", "page"]:  # Skip pagination parameter
            continue
        active_facets[key] = values
        if not key.startswith("text_meta."):
            search_key = f"text_meta.{key}"
        else:
            search_key = key
            
        for value in values:
            filters.append(f'{search_key} = "{value}"')
            
            # Prepare removal URLs for each facet value
            if key not in remove_facet_urls:
                remove_facet_urls[key] = {}
            remove_facet_urls[key][value] = _build_remove_facet_url(request, key, value)

    filter_query = " AND ".join(filters) if filters else None

    # Create search instance and perform search with pagination
    search_instance = Search()
    ft_hits = search_instance.faceted_search(
        query_text, 
        filters=filter_query,
        page=page,
        hits_per_page=hits_per_page
    )
    
    # Process search results
    fulltext_results = []
    facets = []
    has_results = bool(ft_hits.get("hits"))
    total_hits = ft_hits.get("totalHits", 0) if has_results else 0
    total_pages = ft_hits.get("totalPages", 1) if has_results else 1

    if has_results:
        # Process facet distribution
        facet_distribution = ft_hits.get("facetDistribution", {})
        
        for facet_name, values in facet_distribution.items():
            if not values:
                continue
                
            display_name = facet_name.replace("text_meta.", "").replace("_", " ").capitalize()
            facet_values = []
            
            # Store counts for active facets display
            if facet_name not in facet_counts:
                facet_counts[facet_name] = {}
                
            for value, count in values.items():
                facet_counts[facet_name][value] = count
                is_active = facet_name in active_facets and value in active_facets[facet_name]
                
                facet_values.append({
                    "value": value,
                    "count": count,
                    "is_active": is_active,
                    "remove_url": _build_remove_facet_url(request, facet_name, value),
                    "add_url": _build_add_facet_url(request, facet_name, value)
                })

            if facet_values:
                facets.append({
                    "name": display_name,
                    "values": sorted(facet_values, key=lambda x: (-x["count"], x["value"]))
                })

        # Process search hits
        fulltext_results = _process_search_hits(ft_hits["hits"])

    context.update({
        "fulltext_results": fulltext_results,
        "facets": facets,
        "query_text": query_text,
        "active_facets": active_facets,
        "facet_counts": facet_counts,
        "remove_facet_urls": remove_facet_urls,
        "remove_query_url": _build_remove_query_url(request),
        "totalHits": total_hits,
        "has_results": has_results,
        # Add pagination context
        "current_page": page,
        "total_pages": total_pages,
        "has_previous": page > 1,
        "has_next": page < total_pages,
        "previous_page": page - 1,
        "next_page": page + 1,
    })

    return render(request, "faceted_search.html", context)

def _build_remove_facet_url(request, facet, value):
    """Build URL for removing a facet value from the current search."""
    params = request.GET.copy()
    facet_values = params.getlist(facet)
    # Only attempt to remove if the value exists
    if value in facet_values:
        facet_values.remove(value)
    params.setlist(facet, facet_values)
    # Remove page parameter to reset pagination
    if 'page' in params:
        del params['page']
    return f"?{params.urlencode()}"

def _build_add_facet_url(request, facet, value):
    """Build URL for adding a facet value to the current search."""
    params = request.GET.copy()
    params.appendlist(facet, value)
    # Remove page parameter to reset pagination
    if 'page' in params:
        del params['page']
    return f"?{params.urlencode()}"

def _process_search_hits(hits):
    """Process search hits into a consistent format."""
    results = []
    for hit in hits:
        # Get hit positions and determine which fields have matches
        attrs = list(hit["_matchesPosition"].keys())
        
        # Process hits based on matched fields
        hits_dict = {}
        if "text.normalized" in attrs:
            hits_dict["Normalized text"] = hit["_formatted"]["text"][0]["normalized"]
        elif "text.normalized_group" in attrs:
            hits_dict["Normalized text group"] = hit["_formatted"]["text"][0]["normalized_group"]
        elif "text.lemmatized" in attrs:
            hits_dict["Lemmatized"] = hit["_formatted"]["text"][0]["lemmatized"]
        elif "text.english_translation" in attrs:
            hits_dict["English Translation"] = hit["_formatted"]["text"][0]["english_translation"]
        else:
            for attr in attrs:
                if "slug" not in attr:
                    name = attr.split('.')[-1] if '.' in attr else attr
                    hits_dict[name] = hit["_formatted"]["text_meta"].get(name, '') if '.' in attr else hit["_formatted"].get(name, '')

        results.append({
            "title": hit["_formatted"]["title"],
            "author": hit["text_meta"].get("author", ""),
            "urn": hit["text_meta"]["document_cts_urn"],
            "slug": hit["slug"],
            "corpus_slug": hit["corpus_slug"],
            "hits": hits_dict
        })
    
    return results

def add_author_and_urn(texts):
    for text in texts:
        try:
            text.author = text.text_meta.get(name="author").value
        except models.TextMeta.DoesNotExist:
            logger.debug("Authors for Corpus not found")  # Debug statement
            pass
        try:
            text.urn_code = text.text_meta.get(name="document_cts_urn").value
        except models.TextMeta.DoesNotExist:
            pass


def texts_for_urn(urn):
    # Find texts matching the URN using their metadata
    matching_tm_ids = models.TextMeta.objects.filter(
        name="document_cts_urn", value__iregex="^" + urn + r"($|[\.:])"
    ).values_list("id", flat=True)
    texts = models.Text.objects.filter(
        text_meta__name="document_cts_urn", text_meta__id__in=matching_tm_ids
    ).order_by("slug")
    return texts

def handle_urn(query_text):
    query_text = query_text.strip()
    if query_text.startswith("urn:"):
        urn = query_text
        # check for redirects
        if re.match(r"urn:cts:copticLit:ot.*.crosswire", urn):
            return redirect(
                "https://github.com/CopticScriptorium/corpora/releases/tag/v2.5.0"
            )
        urn = settings.DEPRECATED_URNS.get(urn, urn)
        obj = _resolve_urn(urn)
        if obj.__class__.__name__ == "Text":
            return redirect("text", corpus=obj.corpus.slug, text=obj.slug)
        elif obj.__class__.__name__ == "Corpus":
            return redirect("corpus", corpus=obj.slug)
    return None