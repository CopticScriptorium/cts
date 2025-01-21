import logging
import re
from django import forms
from django.http import Http404
from django.urls import reverse
from django.db.models import Case, F, IntegerField, Q, When
from django.shortcuts import get_object_or_404, redirect, render
from django.db.models.functions import Lower
from texts.search_fields import SearchField
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
    # OK This one wants love now.
    # Let's figure out splittability.
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
    texts = models.Text.objects.all().order_by(Lower("title"))
    for query in queries:
        texts = texts.filter(query)
    add_author_and_urn(texts)
    return texts


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
    all_empty_explanation = f'<span class="meta_pair">{query_text}</span> in any field'
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
    text_query = params["text"][0] if "text" in params and params["text"] > [''] else None

    # (1) unwrap the list of length 1 in params['text'] if it exists
    # (2) if params['text'] starts with "urn:", treat it as a special case, first checking for redirects, then
    #     copying it to params['document_cts_urn'] (it is in a list to remain symmetric with all other non-'text' fields)
    if text_query:
        text_query = text_query.strip()
        if text_query.startswith("urn:"):
            urn = text_query
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

            # no redirect, proceed with search
            params["document_cts_urn"] = [urn]

    # returns a list of queries built with Django's Q operator using non-freetext parameters
    queries = _build_queries_for_special_metadata(params)

    # preliminary results--might need to filter more if freetext query is present
    texts = _fetch_and_filter_texts_for_special_metadata_query(queries)
    
    # build base explanation, a string that will be displayed to the user summarizing their search parameters
    explanation = _build_explanation(params)
        
    fulltext_results=[]
    if "text" in params and text_query:
        results, all_empty_explanation = _build_result_for_query_text(
            text_query, texts, explanation
        )
        ft_hits=models.Text.search(text_query)
        if ft_hits["hits"]:
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
                else:
                    # Create a simple key value dict for the results
                    hits = {}
                    for attr in attrs:
                        name = attr.split('.')[-1]
                        hits[name] = result["_formatted"]["text_meta"].get(name, '')
                logging.info(f'Attribute: {attrs} Hits: {hits}')

                if hits:
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
            "fulltext_results": fulltext_results,
            "form": SearchForm(request.GET),
            "no_query": not any(len(v) for v in request.GET.dict().values()),
            "all_empty": not any(len(r["texts"]) for r in results),
            "all_empty_explanation": all_empty_explanation,
            "query_text": text_query,
        }
    )

    return render(request, "search.html", context)

def faceted_search(request):
    context = _base_context()
    fulltext_results=[]
    params = dict(request.GET.lists())
    ft_hits=models.Text.faceted_search(params["text"][0])
    # {'text_meta.annotation': {'Amir Zeldes': 16, 'Lydia Bremer-McCollum, Caroline T. Schroeder': 2, 'Lydia Bremer-McCollum, Nicholas Wagner': 2}, 'text_meta.author': {'Anonymous': 2, 'Paul the apostle': 1, 'Shenoute': 2}, 'text_meta.corpus': {'acts.pilate': 2, 'bohairic.mark': 16, 'shenoute.house': 2}, 'text_meta.msName': {'CM.1643': 2, 'MONB.XG': 1, 'MONB.XU': 1}, 'text_meta.people': {'none': 17, 'Phinehas': 1}, 'text_meta.places': {'none': 18}, 'text_meta.translation': {'none': 2, 'World English Bible (WEB)': 16}}
    context.update(
        {
            "results": [],
            "fulltext_results": fulltext_results,
            "form": SearchForm(request.GET),
            "no_query": not any(len(v) for v in request.GET.dict().values()),
            "all_empty": True,
            "all_empty_explanation": "Not runnig SQL search",
            "query_text": params["text"],
        }
    )
    return render(request, "search.html", context)

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
