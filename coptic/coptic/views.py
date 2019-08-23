from django.shortcuts import render, get_object_or_404, redirect
from texts.search_fields import get_search_fields
import texts.models as models


def _base_context():
    search_fields = get_search_fields()
    context = {
        'search_fields': search_fields[0:5],
        'secondary_search_fields': search_fields[5:]
    }
    return context


def home_view(request):
    'Home/index view'
    context = _base_context()
    context.update({
        'corpora': models.Corpus.objects.all()
    })
    return render(request, 'index.html', context)

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
    urn_parts = doc_urn.split(":")
    urn_dot_parts = urn_parts[3].split(".")

    text_object.urn_cts_work = ":".join(urn_parts[0:3]) # e.g., "urn:cts:copticLit"
    text_object.edition_urn = doc_urn
    text_object.textgroup_urn = urn_dot_parts[0]
    text_object.corpus_urn = urn_dot_parts[1]
    text_object.text_url = "texts/" + text_object.corpus.slug + "/" + text_object.slug

    try:
        next_text_urn = text_object.text_meta.get(name="next").value
        slug = models.Text.objects.get(text_meta__name="document_cts_urn", text_meta__value=next_text_urn).slug
        text_object.next = slug
    except models.TextMeta.DoesNotExist:
        print("oops!")
    try:
        previous_text_urn = text_object.text_meta.get(name="previous").value
        slug = models.Text.objects.get(text_meta__name="document_cts_urn", text_meta__value=previous_text_urn).slug
        text_object.previous = slug
    except (models.TextMeta.DoesNotExist, models.Text.DoesNotExist):
        print("oops!")
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
    text = get_object_or_404(models.Text, text_meta__name="document_cts_urn", text_meta__value=urn)
    return redirect(f'texts/{text.corpus.slug}/{text.slug}')
