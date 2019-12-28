import re
from django import forms
from django.http import Http404
from django.urls import reverse
from django.db.models import Q
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models.functions import Lower
from texts.search_fields import get_search_fields
from coptic.settings.base import DEPRECATED_URNS
import texts.models as models
import texts.urn


def _base_context():
    search_fields = get_search_fields()
    context = {
        'search_fields': search_fields[0:5],
        'secondary_search_fields': search_fields[5:]
    }
    return context


def home_view(request):
    'Home'
    context = _base_context()
    return render(request, 'home.html', context)


def corpus_view(request, corpus=None):
    corpus_object = get_object_or_404(models.Corpus, slug=corpus)
    texts = models.Text.objects.filter(corpus=corpus_object).order_by("id")

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
    except models.TextMeta.DoesNotExist:
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
    raise Http404("No document found for URN <code>" + urn + "</code>")


def get_meta_values(meta):
    unsplit_values = map(lambda x: x['value'], models.TextMeta.objects.filter(name__iexact=meta.name).values("value").distinct())
    if not meta.splittable:
        meta_values = unsplit_values
    else:
        split_meta_values = [v.split(", ") for v in unsplit_values]
        meta_values = set()
        for vals in split_meta_values:
            meta_values = meta_values.union(set(vals))
    meta_values = sorted(list(set(v.strip() for v in meta_values)))
    meta_values = [re.sub(HTML_TAG_REGEX, '', meta_value) for meta_value in meta_values]
    return meta_values


def index_view(request, special_meta=None):
    context = _base_context()

    value_corpus_pairs = dict()

    meta = get_object_or_404(models.SpecialMeta, name=special_meta)
    meta_values = get_meta_values(meta)

    for meta_value in meta_values:
        if meta.splittable:
            corpora = (models.Text.objects.filter(text_meta__name__iexact=meta.name,
                                                  text_meta__value__contains=meta_value)
                       .values("corpus__slug", "corpus__title", "corpus__id", "corpus__urn_code")
                       .distinct())
        else:
            corpora = (models.Text.objects.filter(text_meta__name__iexact=meta.name,
                                                  text_meta__value__iexact=meta_value)
                       .values("corpus__slug", "corpus__title", "corpus__id", "corpus__urn_code")
                       .distinct())

        value_corpus_pairs[meta_value] = []
        for c in corpora:
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
                "author": author
            })

    context.update({
        'special_meta': meta.name,
        'value_corpus_pairs': sorted(value_corpus_pairs.items(), key=lambda x: x[0]),
        'is_corpus': meta.name == "corpus"
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
                if models.SpecialMeta.objects.get(name=meta_name).splittable:
                    meta_name_query = meta_name_query | Q(text_meta__name__iexact=meta_name, text_meta__value__contains=meta_value)
                else:
                    meta_name_query = meta_name_query | Q(text_meta__name__iexact=meta_name, text_meta__value__iexact=meta_value)
        queries.append(meta_name_query)

    return queries


def _get_texts_for_special_metadata_query(queries):
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

        meta_name_explanations = ([f'<span class="meta_pair">{meta_name} = {meta_value}</span>'
                                   for meta_value in meta_values])
        meta_explanations.append("(" + " OR ".join(meta_name_explanations) + ")")
    return " AND ".join(meta_explanations)


def _build_result_for_query_text(query_text, texts, params, explanation):
    results = []
    meta_names = _get_meta_names_for_query_text(query_text)
    for meta_name in meta_names:
        complete_explanation = f'<span class="meta_pair">{params["text"][0]}</span> in "{meta_name}"'
        complete_explanation += ' with ' if explanation else ''
        complete_explanation += explanation

        text_results = texts.filter(text_meta__name__iexact=meta_name,
                                    text_meta__value__contains=query_text)
        add_author_and_urn(text_results)
        results.append({
            'texts': text_results,
            'explanation': complete_explanation
        })
    all_empty_explanation = f'<span class="meta_pair">{params["text"][0]}</span> in any field'
    all_empty_explanation += ' with ' if explanation else ''
    all_empty_explanation += explanation
    return results, all_empty_explanation


def search(request):
    context = _base_context()

    params = dict(request.GET.lists())
    if "text" in params:
        params['text'] = [x.strip() for x in params["text"]]
        if params["text"][0].startswith("urn"):
            return redirect(urn, urn=params["text"][0])

    queries = _build_queries_for_special_metadata(params)

    # preliminary results--might need to filter more if text query is present
    texts = _get_texts_for_special_metadata_query(queries)

    # build base explanations
    explanation = _build_explanation(params)

    query_text = params['text'][0] if 'text' in params else None
    if query_text:
        results, all_empty_explanation = _build_result_for_query_text(query_text, texts, params, explanation)
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
