from django.test import TestCase
from texts.models import HtmlVisualizationFormat, HtmlVisualization, Corpus, SpecialMeta, Text, TextMeta
import json


class TestHtmlVisualizationFormat(TestCase):
    def test_get_all_formats(self):
        formats = HtmlVisualizationFormat.objects.all()
        self.assertEqual(len(formats), 5)  # We have 5 predefined formats

        expected_formats = {
            "norm": "Normalized Text",
            "analytic": "Analytic Visualization",
            "dipl": "Diplomatic Edition",
            "sahidica": "Sahidica Chapter View",
            "verses": "Versified Text",
        }

        actual_formats = {f.slug: f.title for f in formats}
        self.assertEqual(actual_formats, expected_formats)

    def test_get_format_by_slug(self):
        format = HtmlVisualizationFormat.objects.get(slug="norm")
        self.assertEqual(format.title, "Normalized Text")
        self.assertEqual(format.button_title, "normalized")

    def test_get_format_by_button_title(self):
        format = HtmlVisualizationFormat.objects.get(button_title="diplomatic")
        self.assertEqual(format.slug, "dipl")
        self.assertEqual(format.title, "Diplomatic Edition")


class TestCorpusVisualizationFormats(TestCase):
    def setUp(self):
        self.corpus = Corpus.objects.create(
            title="Test Corpus",
            slug="test-corpus",
            urn_code="urn:test:corpus",
            annis_corpus_name="test.corpus",
        )

        self.norm_format = HtmlVisualizationFormat.objects.get(slug="norm")
        self.dipl_format = HtmlVisualizationFormat.objects.get(slug="dipl")

    def test_set_and_get_visualization_formats(self):
        formats = [self.norm_format, self.dipl_format]
        self.corpus.set_visualization_formats(formats)

        # Test raw storage
        stored_data = json.loads(self.corpus.visualization_formats)
        self.assertEqual(stored_data, ["norm", "dipl"])

        # Test retrieval through property
        retrieved_formats = self.corpus.html_visualization_formats
        self.assertEqual(len(retrieved_formats), 2)
        self.assertEqual([f.slug for f in retrieved_formats], ["norm", "dipl"])


class TestHtmlVisualization(TestCase):
    def setUp(self):
        self.norm_format = HtmlVisualizationFormat.objects.get(slug="norm")
        self.visualization = HtmlVisualization.objects.create(
            visualization_format_slug=self.norm_format.slug,
            html="<div>Test content</div>",
        )

    def test_visualization_format_property(self):
        self.assertEqual(
            self.visualization.visualization_format.slug, self.norm_format.slug
        )
        self.assertEqual(
            self.visualization.visualization_format.title, self.norm_format.title
        )

    def test_visualization_format_setter(self):
        dipl_format = HtmlVisualizationFormat.objects.get(slug="dipl")
        self.visualization.visualization_format = dipl_format
        self.assertEqual(self.visualization.visualization_format_slug, "dipl")


class TestSpecialMeta(TestCase):
    def test_get_all_special_metas(self):
        metas = SpecialMeta.objects.all()
        self.assertEqual(len(metas), 8)  # We have 8 predefined special metas

        expected_names = {
            "corpus",
            "author",
            "people",
            "places",
            "msName",
            "annotation",
            "translation",
            "arabic_translation",
        }
        actual_names = {m.name for m in metas}
        self.assertEqual(actual_names, expected_names)

    def test_get_special_meta_by_name(self):
        meta = SpecialMeta.objects.get(name="people")
        self.assertEqual(meta.order, 3)
        self.assertTrue(meta.splittable)

        meta = SpecialMeta.objects.get(name="author")
        self.assertEqual(meta.order, 2)
        self.assertFalse(meta.splittable)

    def test_special_meta_id_consistency(self):
        """Test that getting the same meta twice returns objects with same ID"""
        meta1 = SpecialMeta.objects.get(name="people")
        meta2 = SpecialMeta.objects.get(name="people")
        self.assertEqual(meta1.id, meta2.id)


class TestTextModel(TestCase):
    def setUp(self):
        self.corpus = Corpus.objects.create(
            title="Test Corpus",
            slug="test-corpus",
            urn_code="urn:test:corpus",
            annis_corpus_name="test.corpus",
        )
        self.text1 = Text.objects.create(
            corpus=self.corpus,
            slug="text1",
            title="Text 1",
        )
        self.text2 = Text.objects.create(
            corpus=self.corpus,
            slug="text2",
            title="Text 2",
        )
        self.meta1 = TextMeta.objects.create(
            text=self.text1,
            name="author",
            value="Author 1",
        )
        self.meta2 = TextMeta.objects.create(
            text=self.text2,
            name="author",
            value="Author 2",
        )
        self.special_meta = SpecialMeta.objects.create(
            name="author",
            order=1,
            splittable=False,
        )

    def test_get_authors_for_corpus(self):
        authors = Text.get_authors_for_corpus(self.corpus.id)
        self.assertSetEqual(authors, {"Author 1", "Author 2"})

    def test_get_corpora_for_meta_value(self):
        corpora = Text.get_corpora_for_meta_value("author", "Author 1", False)
        self.assertEqual(len(corpora), 1)
        self.assertEqual(corpora[0]["corpus__slug"], "test-corpus")

    def test_get_value_corpus_pairs(self):
        value_corpus_pairs = Text.get_value_corpus_pairs(self.special_meta)
        self.assertIn("Author 1", value_corpus_pairs)
        self.assertIn("Author 2", value_corpus_pairs)

    def test_get_b64_meta_values(self):
        value_corpus_pairs = Text.get_value_corpus_pairs(self.special_meta)
        b64_meta_values = Text.get_b64_meta_values(value_corpus_pairs)
        self.assertIn("Author 1", b64_meta_values)
        self.assertIn("Author 2", b64_meta_values)

    def test_get_b64_corpora(self):
        value_corpus_pairs = Text.get_value_corpus_pairs(self.special_meta)
        b64_corpora = Text.get_b64_corpora(value_corpus_pairs)
        self.assertIn("test.corpus", b64_corpora)

    def test_get_all_corpora(self):
        value_corpus_pairs = Text.get_value_corpus_pairs(self.special_meta)
        all_corpora = Text.get_all_corpora(value_corpus_pairs)
        self.assertIn("test.corpus", all_corpora)
