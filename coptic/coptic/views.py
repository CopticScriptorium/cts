from django import forms
from django.db.models import Q
from django.shortcuts import render, get_object_or_404, redirect
from texts.search_fields import get_search_fields
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
    context.update({
        'corpora': models.Corpus.objects.all()
    })
    return render(request, 'home.html', context)


def corpus_view(request, corpus=None):
    corpus_object = get_object_or_404(models.Corpus, slug=corpus)
    texts = models.Text.objects.filter(corpus=corpus_object)

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
        next_text_urn = text_object.text_meta.get(name="next").value
        slug = models.Text.objects.get(text_meta__name="document_cts_urn", text_meta__value=next_text_urn).slug
        text_object.next = slug
    except models.TextMeta.DoesNotExist:
        pass
    try:
        previous_text_urn = text_object.text_meta.get(name="previous").value
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


def urn(request, urn=None):
    try:
        text = models.Text.objects.get(text_meta__name="document_cts_urn", text_meta__value=urn)
        return text_view(request, text=text.slug, corpus=text.corpus.slug)
    except models.Text.DoesNotExist:
        corpus = get_object_or_404(models.Corpus, urn_code=urn)
        return corpus_view(request, corpus=corpus.slug)


def get_meta_values(meta):
    unsplit_values = map(lambda x: x['value'], models.TextMeta.objects.filter(name__iexact=meta.name).values("value").distinct())
    if not meta.splittable:
        meta_values = unsplit_values
    else:
        split_meta_values = [v.split(", ") for v in unsplit_values]
        meta_values = set()
        for vals in split_meta_values:
            meta_values = meta_values.union(set(vals))
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
                       .values("corpus__slug", "corpus__title")
                       .distinct())
        else:
            corpora = (models.Text.objects.filter(text_meta__name__iexact=meta.name,
                                                  text_meta__value__iexact=meta_value)
                       .values("corpus__slug", "corpus__title")
                       .distinct())
        value_corpus_pairs[meta_value] = [{"slug": c['corpus__slug'], "title": c['corpus__title']} for c in corpora]

    context.update({
        'special_meta': meta.name,
        'value_corpus_pairs': sorted(value_corpus_pairs.items(), key=lambda x: x[0]),
        'no_lists': meta.name == "corpus"
    })
    return render(request, 'index.html', context)


class SearchForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for sm in models.SpecialMeta.objects.all():
            meta_values = get_meta_values(sm)
            self.fields[sm.name] = forms.MultipleChoiceField(
                label=sm.name,
                required=False,
                choices=[(v, v) for v in meta_values],
                widget=forms.SelectMultiple(attrs={'class': 'search-choice-field'})
            )

    text = forms.CharField(label="Query", required=False)


def search(request):
    context = _base_context()

    query = Q()
    for meta_name, meta_values in request.GET.dict().items():
        if meta_name == 'text':
            continue
        meta_values = meta_values if isinstance(meta_values, list) else [meta_values]
        for meta_value in meta_values:
            if meta_value:
                if models.SpecialMeta.objects.get(name=meta_name).splittable:
                    query = query | Q(text_meta__name__iexact=meta_name, text_meta__value__contains=meta_value)
                else:
                    query = query | Q(text_meta__name__iexact=meta_name, text_meta__value__iexact=meta_value)
    texts = models.Text.objects.filter(query)

    context.update({
        'results': texts,
        'form': SearchForm(request.GET)
    })

    return render(request, 'search.html', context)