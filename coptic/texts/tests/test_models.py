from django.test import TestCase
from django.conf import settings
from texts.models import HtmlVisualization, Corpus, Text, TextMeta
import json


class TestHtmlVisualizationFormat(TestCase):
    def test_get_all_formats(self):
        formats = settings.HTML_VISUALISATION_FORMATS
        self.assertEqual(len(formats), 5)  # We have 5 predefined formats

        expected_formats = {
            "norm": "Normalized Text",
            "analytic": "Analytic Visualization",
            "dipl": "Diplomatic Edition",
            "sahidica": "Sahidica Chapter View",
            "verses": "Versified Text",
        }

        actual_formats = {formats[f]["slug"]: formats[f]["title"] for f in formats}
        self.assertEqual(actual_formats, expected_formats)

    def test_get_format_by_slug(self):
        format = HtmlVisualization.get_format_by_attribute("slug","norm")
        self.assertEqual(format["title"], "Normalized Text")
        self.assertEqual(format["button_title"], "normalized")

    def test_get_format_by_button_title(self):
        format = HtmlVisualization.get_format_by_attribute("button_title","diplomatic")
        self.assertEqual(format["slug"], "dipl")
        self.assertEqual(format["title"], "Diplomatic Edition")


class TestCorpusVisualizationFormats(TestCase):
    def setUp(self):
        self.corpus = Corpus.objects.create(
            title="Test Corpus",
            slug="test-corpus",
            urn_code="urn:test:corpus",
            annis_corpus_name="test.corpus",
        )

        self.norm_format = HtmlVisualization.get_format_by_attribute("slug","norm")
        self.dipl_format = HtmlVisualization.get_format_by_attribute("slug","dipl")

    def test_set_and_get_visualization_formats(self):
        formats = [self.norm_format, self.dipl_format]
        self.corpus.set_visualization_formats(formats)

        # Test raw storage
        stored_data = self.corpus.visualization_formats
        self.assertEqual(stored_data, 'norm,dipl')

        # Test retrieval through property
        retrieved_formats = self.corpus.html_visualization_formats
        self.assertEqual(len(retrieved_formats), 2)
        self.assertEqual([f["slug"] for f in retrieved_formats], ["norm", "dipl"])


class TestHtmlVisualization(TestCase):
    def setUp(self):
        self.norm_format = HtmlVisualization.get_format_by_attribute("slug","norm")
        self.visualization = HtmlVisualization.objects.create(
            visualization_format_slug=self.norm_format["slug"],
        )

    def test_visualization_format_property(self):
        self.assertEqual(
            self.visualization.visualization_format["slug"], self.norm_format["slug"]
        )
        self.assertEqual(
            self.visualization.visualization_format["title"], self.norm_format["title"]
        )

    def test_visualization_format_setter(self):
        dipl_format = HtmlVisualization.get_format_by_attribute("slug","dipl")
        self.visualization.visualization_format = dipl_format
        self.assertEqual(self.visualization.visualization_format_slug, "dipl")



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
            value="Author 2", # we have here a duplicate Author 2
        )
        self.meta3 = TextMeta.objects.create(
            text=self.text2,
            name="author",
            value="Author 3", # we have here a duplicate Author 2
        )
        self.text1.text_meta.add(self.meta1)
        self.text2.text_meta.add(self.meta2)
        self.text2.text_meta.add(self.meta3)
        self.special_meta ={"name":"author","order":1,"split":";"}

    def test_get_value_corpus_pairs(self):
        value_corpus_pairs = Text.get_value_corpus_pairs(self.special_meta)
        self.assertIn("Author 1", value_corpus_pairs)
        self.assertIn("Author 2", value_corpus_pairs)
        self.assertIn("Author 3", value_corpus_pairs)

    def test_get_sorted_value_corpus_pairs(self):
        # FIXME So this doesn't work bevause in the database we have Author 1; Author 2
        # And we are using "IN" in the query
        value_corpus_pairs = Text.get_value_corpus_pairs(self.special_meta)
        self.assertEqual(list(value_corpus_pairs.keys())[0], "Author 1")
        self.assertEqual(list(value_corpus_pairs.keys())[1], "Author 2")
    
    class TestTextModel(TestCase):
            def setUp(self):
                self.corpus = Corpus.objects.create(
                    title="Test Corpus",
                    slug="test-corpus",
                    urn_code="urn:test:corpus",
                    annis_corpus_name="test.corpus",
                )
                self.text = Text.objects.create(
                    corpus=self.corpus,
                    slug="text1",
                    title="Text 1",
                    tt_dir="dir1",
                    tt_filename="file1",
                    tt_dir_tree_id="tree1",
                    document_cts_urn="urn:cts:test",
                )
                self.text.text = """
                <chapter_n chapter_n="1">
                    <norm lemma="lemma1" norm="norm1" norm_group="group1">text1</norm>
                </chapter_n>
                <chapter_n chapter_n="2">
                    <norm lemma="lemma2" norm="norm2" norm_group="group2">text2</norm>
                </chapter_n>
                """

            def test_get_text_chapters(self):
                chapters = self.text.get_text_chapters()
                expected_chapters = {
                    '\n            <norm lemma="lemma1" norm="norm1" norm_group="group1">text1</norm>\n        ',
                    '\n            <norm lemma="lemma2" norm="norm2" norm_group="group2">text2</norm>\n        '
                }
                self.assertEqual(chapters, expected_chapters)

            def test_get_text_lemmatized(self):
                lemmatized_text = self.text.get_text_lemmatized(self.text.text)
                self.assertEqual(lemmatized_text, "lemma1 lemma2")

            def test_get_text_normalized_group(self):
                normalized_group_text = self.text.get_text_normalized_group(self.text.text)
                self.assertEqual(normalized_group_text, "group1 group2")

            def test_get_text_normalized(self):
                normalized_text = self.text.get_text_normalized(self.text.text)
                self.assertEqual(normalized_text, "norm1 norm2")

            def test_to_json(self):
                json_data = self.text.to_json()
                expected_json = {
                    "id": self.text.id,
                    "title": self.text.title,
                    "slug": self.text.slug,
                    "created": self.text.created.isoformat(),
                    "modified": self.text.modified.isoformat(),
                    "corpus": self.corpus.title,
                    "corpus_slug": self.corpus.slug,
                    "text_meta": {},
                    "text": [
                        {
                            "lemmatized": "lemma1 lemma2",
                            "normalized": "norm1 norm2",
                            "normalized_group": "group1 group2",
                        }
                    ],
                    "tt_dir": self.text.tt_dir,
                    "tt_filename": self.text.tt_filename,
                    "tt_dir_tree_id": self.text.tt_dir_tree_id,
                    "document_cts_urn": self.text.document_cts_urn,
                }
                self.assertEqual(json_data, expected_json)
