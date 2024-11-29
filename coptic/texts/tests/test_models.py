from django.test import TestCase
from texts.models import HtmlVisualizationFormat, HtmlVisualization, Corpus, SpecialMeta
import json


class TestHtmlVisualizationFormat(TestCase):
    def test_get_all_formats(self):
        formats = HtmlVisualizationFormat.objects.all()
        self.assertEqual(len(formats), 5)  # We have 5 predefined formats

        # Updated to match the actual slugs from HtmlVisualizationFormat.Data.FORMATS
        expected_formats = {
            "norm": "Normalized Text",
            "analytic": "Analytic Visualization",
            "dipl": "Diplomatic Edition",
            "sahidica": "Sahidica Chapter View",
            "verses": "Versified Text",  # Changed from 'versified' to 'verses'
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
