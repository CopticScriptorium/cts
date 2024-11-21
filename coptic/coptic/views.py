import re
from django import forms
from django.http import Http404
from django.urls import reverse
from django.db.models import Q, Case, When, IntegerField, F
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models.functions import Lower
from texts.search_fields import SearchField
from coptic.settings.base import DEPRECATED_URNS
from collections import OrderedDict
import texts.urn as urnlib
import texts.models as models
import texts.urn
import base64

from django.template.defaulttags import register

@register.filter(name='keyvalue')
def keyvalue(dict, key):
    return dict.get(key)

def home_view(request):
    'Home'
    context = _base_context()
    return render(request, 'home.html', context)


def corpus_view(request, corpus=None):
    corpus_object = get_object_or_404(models.Corpus, slug=corpus)

    # This is almost what we need, but because of some ORM quirks (LEFT OUTER JOINs where we needed INNER JOINs)
    # every text with a valid `order` metadatum will appear twice in these results: once with an "order" annotation,
    # and once without.
    texts = (
        models.Text.objects
        .filter(corpus=corpus_object)
        .annotate(order=Case(
            When(text_meta__name="order", then="text_meta__value"),
            output_field=IntegerField()
        ))
        .distinct()
        .order_by("order", "id")
    )

    # to handle this, for every id, take the one with an "order" if it has one, else fall back to the one without order
    ids = set([t.id for t in texts])
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

    context = _base_context()
    context.update({
        'corpus': corpus_object,
        'texts': texts
    })
    return render(request, 'corpus.html', context)


def text_view(request, corpus=None, text=None, format=None):
    text_object = get_object_or_404(models.Text, slug=text)
    if not format:
        visualization = text_object.html_visualizations.all()[0]
        format = visualization.visualization_format.slug
        return text_view(request, corpus=corpus, text=text, format=format)

    visualization = text_object.html_visualizations.get(visualization_format__slug=format)

    doc_urn = text_object.text_meta.get(name="document_cts_urn").value

    text_object.edition_urn = doc_urn
    text_object.urn_cts_work = texts.urn.cts_work(doc_urn)
    text_object.textgroup_urn = texts.urn.textgroup_urn(doc_urn)
    text_object.corpus_urn = texts.urn.corpus_urn(doc_urn)
    text_object.text_url = "texts/" + text_object.corpus.slug + "/" + text_object.slug

    try:
        next_text_urn = text_object.text_meta.get(name="next").value.strip()
        slug = models.Text.objects.get(text_meta__name="document_cts_urn", text_meta__value=next_text_urn).slug
        text_object.next = slug
    except (models.TextMeta.DoesNotExist, models.Text.DoesNotExist):
        pass
    try:
        previous_text_urn = text_object.text_meta.get(name="previous").value.strip()
        slug = models.Text.objects.get(text_meta__name="document_cts_urn", text_meta__value=previous_text_urn).slug
        text_object.previous = slug
    except (models.TextMeta.DoesNotExist, models.Text.DoesNotExist):
        pass
    try:
        text_object.endnote = text_object.text_meta.get(name="endnote").value
    except (models.TextMeta.DoesNotExist, models.Text.DoesNotExist):
        pass

    context = _base_context()
    context.update({
        'text': text_object,
        'visualization': visualization,
        'format': format
    })
    return render(request, 'text.html', context)


def not_found(request):
    return render(request, '404.html', {})


def _resolve_urn(urn):
    try:
        text = models.Text.objects.get(text_meta__name="document_cts_urn", text_meta__value=urn)
        return text
    except models.Text.DoesNotExist:
        try:
            corpus = models.Corpus.objects.get(urn_code=urn)
            return corpus
        except models.Corpus.DoesNotExist:
            return None


def urn(request, urn=None):
    # https://github.com/CopticScriptorium/cts/issues/112
    if re.match(r'urn:cts:copticLit:ot.*.crosswire', urn):
        return redirect('https://github.com/CopticScriptorium/corpora/releases/tag/v2.5.0')

    # check to see if the URN is deprecated and redirect if so
    urn = DEPRECATED_URNS.get(urn, urn)
    obj = _resolve_urn(urn)

    if obj.__class__.__name__ == "Text":
        return redirect('text', corpus=obj.corpus.slug, text=obj.slug)
    elif obj.__class__.__name__ == "Corpus":
        return redirect('corpus', corpus=obj.slug)
    return redirect(reverse('search') + f"?text={urn}")


def get_meta_values(meta):
    unsplit_values = map(lambda x: x['value'], models.TextMeta.objects.filter(name__iexact=meta.name).values("value").distinct())
    if not meta.splittable:
        meta_values = unsplit_values
    else:
        sep = "; " if str(meta.name) in ["places","people"] else ", "
        split_meta_values = [v.split(sep) for v in unsplit_values]
        for i, vals in enumerate(split_meta_values):
            if any(len(v) > 50 for v in vals) and sep == ", ":  # e.g. long translation value with comma somewhere
                split_meta_values[i] = [", ".join(vals)]
        meta_values = set()
        for vals in split_meta_values:
            meta_values = meta_values.union(set(vals))
    meta_values = sorted(list(set(v.strip() for v in meta_values)))
    meta_values = [re.sub(HTML_TAG_REGEX, '', meta_value) for meta_value in meta_values]
    return meta_values


def index_view(request, special_meta=None):
    context = _base_context()

    value_corpus_pairs = OrderedDict()

    meta = get_object_or_404(models.SpecialMeta, name=special_meta)
    meta_values = get_meta_values(meta)

    b64_meta_values = {}
    b64_corpora = {}
    all_corpora = set([])

    for meta_value in meta_values:
        b64_meta_values[meta_value] = str(base64.b64encode(('identity="'+meta_value+'"').encode("ascii")).decode("ascii"))
        if meta.splittable:
            corpora = (models.Text.objects.filter(text_meta__name__iexact=meta.name,
                                                  text_meta__value__icontains=meta_value)
                       .values("corpus__slug", "corpus__title", "corpus__id", "corpus__urn_code", "corpus__annis_corpus_name")
                       .distinct())
        else:
            corpora = (models.Text.objects.filter(text_meta__name__iexact=meta.name,
                                                  text_meta__value__iexact=meta_value)
                       .values("corpus__slug", "corpus__title", "corpus__id", "corpus__urn_code", "corpus__annis_corpus_name")
                       .distinct())

        value_corpus_pairs[meta_value] = []
        for c in sorted(corpora,key=lambda x: x['corpus__title']):
            try:
                authors = map(lambda x: x.text_meta.get(name__iexact="author").value,
                        models.Text.objects.filter(corpus__id=c["corpus__id"]))
                authors = list(set(authors))

                if len(authors) == 0:
                    author = None
                elif len(authors) == 1:
                    author = authors[0]
                elif len(authors) < 3:
                    author = ", ".join(authors)
                else:
                    author = "multiple"
            except models.TextMeta.DoesNotExist:
                author = None

            value_corpus_pairs[meta_value].append({
                "slug": c['corpus__slug'],
                "title": c['corpus__title'],
                "urn_code": c['corpus__urn_code'],
                "author": author,
                "annis_corpus_name": c["corpus__annis_corpus_name"]
            })

            b64_corpora[c["corpus__annis_corpus_name"]] = str(base64.b64encode(c["corpus__annis_corpus_name"].encode("ascii")).decode("ascii"))
            all_corpora.add(c["corpus__annis_corpus_name"])
        value_corpus_pairs[meta_value].sort(key=lambda x:x["title"])

    annis_corpora = ",".join(list(all_corpora))
    annis_corpora = str(base64.b64encode(annis_corpora.encode("ascii")).decode("ascii"))
    context.update({
        'special_meta': meta.name,
        'value_corpus_pairs': sorted(value_corpus_pairs.items(), key=lambda x: x[1][0]["title"]),
        'is_corpus': meta.name == "corpus",
        'b64_meta_values': b64_meta_values,
        'b64_corpora': b64_corpora,
        'annis_corpora': annis_corpora  # """YXBvcGh0aGVnbWF0YS5wYXRydW0sYmVzYS5sZXR0ZXJzLGNvcHRpYy50cmVlYmFuayxkb2MucGFweXJpLGRvcm1pdGlvbi5qb2huLGpvaGFubmVzLmNhbm9ucyxsaWZlLmFwaG91LGxpZmUuY3lydXMsbGlmZS5sb25naW51cy5sdWNpdXMsbGlmZS5vbm5vcGhyaXVzLGxpZmUucGF1bC50YW1tYSxsaWZlLnBoaWIsbWFydHlyZG9tLnZpY3RvcixwYWNob21pdXMuaW5zdHJ1Y3Rpb25zLHByb2NsdXMuaG9taWxpZXMscHNldWRvLmF0aGFuYXNpdXMuZGlzY291cnNlcyxwc2V1ZG8uZXBocmVtLHBzZXVkby50aGVvcGhpbHVzLHNhaGlkaWNhLjFjb3JpbnRoaWFucyxzYWhpZGljYS5tYXJrLHNoZW5vdXRlLmEyMixzaGVub3V0ZS5hYnJhaGFtLHNoZW5vdXRlLmRpcnQsc2hlbm91dGUuZWFnZXJuZXNzLHNoZW5vdXRlLmZveCxzaGVub3V0ZS5zZWVrcyxzaGVub3V0ZS50aG9zZSxzaGVub3V0ZS51bmtub3duNV8x"""
    })
    return render(request, 'index.html', context)


# search --------------------------------------------------------------------------------
def _get_meta_names_for_query_text(text):
    names = [sm.name for sm in models.SpecialMeta.objects.all()]
    if "title" not in names:
        names.append("title")
    if "author" not in names:
        names.append("author")
    if text.lower().startswith('urn:'):
        names.append("document_cts_urn")
    return names


HTML_TAG_REGEX = re.compile(r'<[^>]*?>')
class SearchForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for sm in models.SpecialMeta.objects.all().order_by(Lower("name")):
            meta_values = get_meta_values(sm)
            choices = []
            for v in meta_values:
                if sm.name == "corpus":
                    try:
                        human_name = models.Corpus.objects.get(annis_corpus_name=v).title
                    except models.Corpus.DoesNotExist:
                        human_name = v
                else:
                    human_name = v
                human_name = re.sub(HTML_TAG_REGEX, '', human_name)
                choices.append((v, human_name))

            self.fields[sm.name] = forms.MultipleChoiceField(
                label=sm.name,
                required=False,
                choices=choices,
                widget=forms.SelectMultiple(attrs={'class': 'search-choice-field'})
            )

    text = forms.CharField(
        label="query",
        required=False,
        widget=forms.TextInput(attrs={'class': 'search-text-field'})
    )


def _build_queries_for_special_metadata(params):
    queries = []
    for meta_name, meta_values in params.items():
        if meta_name == 'text':
            continue

        meta_values = sorted([s.strip() for s in meta_values])
        meta_name_query = Q()
        for meta_value in meta_values:
            if meta_value:
                if meta_name == 'document_cts_urn':
                    regex = "^" + meta_value.replace(".", r"\.").replace("*", ".*")
                    meta_name_query = meta_name_query | Q(text_meta__name__iexact=meta_name, text_meta__value__regex=regex)
                elif models.SpecialMeta.objects.get(name=meta_name).splittable:
                    meta_name_query = meta_name_query | Q(text_meta__name__iexact=meta_name, text_meta__value__icontains=meta_value)
                else:
                    meta_name_query = meta_name_query | Q(text_meta__name__iexact=meta_name, text_meta__value__iexact=meta_value)
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
                    meta_value = models.Corpus.objects.get(annis_corpus_name=meta_value).title
                except models.Corpus.DoesNotExist:
                    pass
                new_meta_values.append(meta_value)
            meta_values = new_meta_values

        # indicate the special logic used for document_cts_urn
        sep = '=' if meta_name != 'document_cts_urn' else 'matching'
        meta_name_explanations = (
            [
                f'<span class="meta_pair">{meta_name}</span> {sep} <span class="meta_pair">{meta_value}</span>'
                for meta_value in meta_values
            ]
        )
        meta_explanations.append("(" + " OR ".join(meta_name_explanations) + ")")
    return " AND ".join(meta_explanations)


def _build_result_for_query_text(params, texts, explanation):
    query_text = params["text"]
    results = []
    meta_names = _get_meta_names_for_query_text(query_text)
    for meta_name in meta_names:
        complete_explanation = f'<span class="meta_pair">{query_text}</span> in "{meta_name}"'
        complete_explanation += ' with ' if explanation else ''
        complete_explanation += explanation

        if meta_name == 'document_cts_urn':
            text_results = texts
        else:
            text_results = texts.filter(text_meta__name__iexact=meta_name,
                                        text_meta__value__icontains=query_text)
        add_author_and_urn(text_results)
        results.append({
            'texts': text_results,
            'explanation': complete_explanation
        })
    all_empty_explanation = f'<span class="meta_pair">{query_text}</span> in any field'
    all_empty_explanation += ' with ' if explanation else ''
    all_empty_explanation += explanation
    return results, all_empty_explanation


def _base_context():
    search_fields = [SearchField("corpus"), SearchField("author"), SearchField("people"), SearchField("places"), SearchField("msName"), SearchField("annotation"), SearchField("translation"), SearchField("arabic_translation")]
    context = {
        'search_fields': search_fields[:5],
        'secondary_search_fields': search_fields[5:]
    }
    return context


def search(request):
    context = _base_context()

    # possible keys are "text", which is the freetext that a user entered,
    # and slugs corresponding to SpecialMetas (e.g. "author", "translation", ...)
    # which the user can select in the sidebar on right-hand side of the screen
    params = dict(request.GET.lists())

    # (1) unwrap the list of length 1 in params['text'] if it exists
    # (2) if params['text'] starts with "urn:", treat it as a special case, first checking for redirects, then
    #     copying it to params['document_cts_urn'] (it is in a list to remain symmetric with all other non-'text' fields)
    if "text" in params:
        assert len(params['text']) == 1
        params['text'] = params["text"][0].strip()
        if params['text'].startswith('urn:'):
            urn = params['text']
            # check for redirects
            if re.match(r'urn:cts:copticLit:ot.*.crosswire', urn):
                return redirect('https://github.com/CopticScriptorium/corpora/releases/tag/v2.5.0')
            urn = DEPRECATED_URNS.get(urn, urn)
            obj = _resolve_urn(urn)
            if obj.__class__.__name__ == "Text":
                return redirect('text', corpus=obj.corpus.slug, text=obj.slug)
            elif obj.__class__.__name__ == "Corpus":
                return redirect('corpus', corpus=obj.slug)

            # no redirect, proceed with search
            params['document_cts_urn'] = [urn]

    # returns a list of queries built with Django's Q operator using non-freetext parameters
    queries = _build_queries_for_special_metadata(params)

    # preliminary results--might need to filter more if freetext query is present
    texts = _fetch_and_filter_texts_for_special_metadata_query(queries)

    # build base explanation, a string that will be displayed to the user summarizing their search parameters
    explanation = _build_explanation(params)

    if 'text' in params:
        results, all_empty_explanation = _build_result_for_query_text(params, texts, explanation)
    else:
        results = [{
            'texts': texts,
            'explanation': explanation
        }]
        all_empty_explanation = explanation

    context.update({
        'results': results,
        'form': SearchForm(request.GET),
        'no_query': not any(len(v) for v in request.GET.dict().values()),
        'all_empty': not any(len(r['texts']) for r in results),
        'all_empty_explanation': all_empty_explanation,
    })

    return render(request, 'search.html', context)


def add_author_and_urn(texts):
    for text in texts:
        try:
            text.author = text.text_meta.get(name="author").value
        except models.TextMeta.DoesNotExist:
            pass
        try:
            text.urn_code = text.text_meta.get(name="document_cts_urn").value
        except models.TextMeta.DoesNotExist:
            pass
