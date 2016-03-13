import logging
import re
from django.shortcuts import redirect
from texts.models import Text, TextMeta, SearchFieldValue

logger = logging.getLogger(__name__)


def urn_redirect(request, query):
    'Redirect to the correct place based on a URN'
    value = urn_redirect_value(query)
    logger.info('Redirecting to %s from %s' % (value, query))
    return redirect(value)


def _all_segments_match(subset, urn):
    subset_segments, urn_segments = [re.split('[.:]', v) for v in (subset, urn)]

    if len(subset_segments) > len(urn_segments):
        return False

    for a, b in zip(subset_segments, urn_segments):
        if a != b:
            return False

    return True


def _corpora_filter(corpora):
    def sfv(corpus):
        return SearchFieldValue.objects.get(title=corpus.annis_corpus_name, search_field__title='corpus')

    def f(corpus):
        s = sfv(corpus)
        return 'corpus=%s:%s' % (s.id, s.title)

    args = [f(corpus) for corpus in corpora]
    return '/filter/' + '&'.join(args)


def urn_redirect_value(query):
    'This is a work in progress, in conjunction with app.js changes'
    ss = 'urn' + query

    text_metas = tuple(TextMeta.objects.filter(name='document_cts_urn', value__startswith=ss))
    matching_tm_ids = [tm.id for tm in text_metas if _all_segments_match(ss, tm.value)]
    texts = tuple(
        Text.objects.filter(text_meta__name='document_cts_urn', text_meta__id__in=matching_tm_ids).order_by('id'))

    if len(texts) == 1:
        text_slug = texts[0].slug
        corpus_slug = texts[0].corpus.slug
        return 'texts/%s/%s' % (corpus_slug, text_slug)
    else:
        corpora = list(set([t.corpus for t in texts]))
        return _corpora_filter(corpora)


def passage_text(passage):
    """
    Look up the passage URN against the document_cts_urn metadatum from ANNIS
    """

    # Check the passage urn against each text metadatum
    for text in Text.objects.all():
        for meta in text.text_meta.filter(name='document_cts_urn'):
            if meta.value.split(":")[3] == passage:
                return text


import unittest


class ViewsTest(unittest.TestCase):
    def run_and_assert(self, input, expected):
        self.assertEqual(urn_redirect_value(input), expected)

    def test_corpus_urn(self):
        self.run_and_assert('urn:cts:copticLit:shenoute.fox', '/filter/corpus_urn=0:shenoute.fox')

    def test_a(self):
        self.run_and_assert('urn:cts:copticLit:nt.mark.sahidica_ed:1', 'texts/gospel_of_mark/mark_01')

    def test_a2(self):
        self.run_and_assert('urn:cts:copticLit:nt.mark.sahidica_ed', '?')

    def test_a3(self):
        self.run_and_assert('urn:cts:copticLit:nt.mark', '/filter/corpus_urn=0:nt.mark')

    def test_a4(self):
        self.run_and_assert('urn:cts:copticLit:nt', '?')

    def test_a5(self):
        self.run_and_assert('urn:cts:copticLit', '?')

    def test_a6(self):
        self.run_and_assert('urn:cts', '?')

    def test_b(self):
        self.run_and_assert('urn:cts:copticLit:shenoute.abraham.monbxl_93_94', '?')

    def test_garbage_returns_slash(self):
        self.run_and_assert('garbage', '/')


if __name__ == '__main__':
    unittest.main()
