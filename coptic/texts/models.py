import datetime
import re
import logging
from collections import OrderedDict
from base64 import b64encode
from django.db import models
from django.conf import settings
from cache_memoize import cache_memoize

from texts.ft_search import Search
from gh_ingest.htmlvis import generate_visualization
from gh_ingest.scraper_exceptions import NoTexts
from gh_ingest.repository import Repository

# Configure logger
logger = logging.getLogger(__name__)

HTML_TAG_REGEX = re.compile(r"<[^>]*?>")


class Corpus(models.Model):
    created = models.DateTimeField(editable=False)
    modified = models.DateTimeField(editable=False)
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=40, db_index=True, unique=True)
    urn_code = models.CharField(max_length=200, db_index=True)
    annis_corpus_name = models.CharField(max_length=200, db_index=True)
    github = models.CharField(max_length=200)
    github_tei = models.CharField(max_length=50, blank=True)
    github_relannis = models.CharField(max_length=50, blank=True)
    github_paula = models.CharField(max_length=50, blank=True)
    # Store visualization formats as a comma-separated string
    visualization_formats = models.TextField(default="", db_index=True)
    author = models.TextField(default="",db_index=True)
    
    #TODO: here we want to add a fielf for the actual text.

    def __init__(self, *args, **kwargs):
        # the repository is a signleton, so we can just create it here
        self.repository=Repository()
        super().__init__(*args, **kwargs)
        
    def get_visualization_formats(self):
        """Retrieve visualization formats as a list of slugs."""
        if not self.visualization_formats:
            return []
        return self.visualization_formats.split(",")

    def set_visualization_formats(self, formats):
        """Set visualization formats from a list of HtmlVisualizationFormat objects."""
        self.visualization_formats = ",".join(f["slug"] for f in formats)
        
    def index(self):
        # Index texts in Meilisearch
        search = Search()
        json_array=[]
        if search.search_available:
            texts = self.text_set.all()
            for text in texts:
                json_array.append(text.to_json())
            result = search.index_text(json_array)
            logging.info(f"Indexed {self.slug}: {len(texts)} texts.")
        else:
            logging.error("Search is not available. Skipping indexing.")

    @property
    def html_visualization_formats(self):
        """Return HtmlVisualizationFormat objects in the stored order."""
        return [
            HtmlVisualization.get_format_by_attribute("slug",slug)
            for slug in self.get_visualization_formats()
        ]

    class Meta:
        verbose_name_plural = "Corpora"

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        """On save, update timestamps"""
        if not self.id:
            self.created = datetime.datetime.today()
        self.modified = datetime.datetime.today()
        super().save(*args, **kwargs)

    def _annis_corpus_name_b64encoded(self):
        return b64encode(str.encode(self.annis_corpus_name)).decode()

    def annis_link(self):
        return (
            "https://annis.copticscriptorium.org/annis/scriptorium#_c="
            + self._annis_corpus_name_b64encoded()
        )

class HtmlVisualization(models.Model):
    #FIXME this model is probably not needed at all ..
    # get_html_visualization should be a method on Text
    # At any rate we want to actually store the CSS and configuration used in the database
    # So at runtime we can still generate the visualizations dynamically.
    visualization_format_slug = models.CharField(max_length=200)
    config = models.TextField(blank=True)
    css = models.TextField(blank=True)
    html = models.TextField(blank=True)

    class Meta:
        verbose_name = "HTML Visualization"

    @classmethod
    def get_format_by_attribute(cls, attribute, value):
        # now lets get the one with the slug passed in the parameter
        format = next((f for f in settings.HTML_VISUALISATION_FORMATS.values() if f[attribute] == value), None)
        if format is None:
            raise ValueError(f"Visualization format with '{attribute}' = '{value}' not found.")
        return format

    @property
    def html_live(self):
        texts = self.text_set.all()
        return generate_visualization(texts.get(), self.config, self.visualization_format_slug)
    
    
    @property
    def visualization_format(self):
        return HtmlVisualization.get_format_by_attribute("slug",self.visualization_format_slug)

    @visualization_format.setter
    def visualization_format(self, format_obj):
        """Set the visualization format using a HtmlVisualizationFormat object"""
        if format_obj is None:
            self.visualization_format_slug = None
        else:
            self.visualization_format_slug = format_obj["slug"]

    def __str__(self):
        return self.visualization_format["title"]


class TextMeta(models.Model):
    name = models.CharField(max_length=200, db_index=True)
    value = models.CharField(max_length=10000, db_index=True)

    class Meta:
        verbose_name = "Text Meta Item"

    def __str__(self):
        return self.name + ": " + self.value

    def value_customized(self):
        v = self.value
        if re.match(r"https?://", v):  # Turn URLs into <a> tags
            return '<a href="{}">{}</a>'.format(v, v)

        if v.startswith("urn:cts"):  # Turn cts URNs into <a> tags
            return '<a href="/{}">{}</a>'.format(v, v)

        return v

class Text(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=40, db_index=True)
    created = models.DateTimeField(editable=False)
    modified = models.DateTimeField(editable=False)
    corpus = models.ForeignKey(Corpus, blank=True, null=True, on_delete=models.CASCADE)
    html_visualizations = models.ManyToManyField(HtmlVisualization, blank=True)
    # FIXME: This is not actually a many to many relationship but a one to
    # many relationship in the entity-attribute-value model.
    text_meta = models.ManyToManyField(TextMeta, blank=True, db_index=True)
    tt_dir = models.CharField(max_length=40)
    tt_filename = models.CharField(max_length=40)
    tt_dir_tree_id = models.CharField(max_length=40)
    document_cts_urn = models.CharField(max_length=80)
    content=models.TextField(default="")

    @classmethod
    @cache_memoize(settings.CACHE_TTL)
    def get_meta_values(cls, meta):
        return  TextMeta.objects.filter(name__iexact=meta["name"]).values("value").distinct().values_list("value", flat=True)

    @classmethod
    def split_and_clean_meta_values(self, unsplit_values, meta):
        # FIXME make it clear we have a local hack for
        # A single abnormal value rather than some logic about 50 characters.
        if meta["splitter"]:
            split_meta_values = [
                item.strip()
                for v in unsplit_values
                for item in v.split(meta["splitter"])
                if v
                != "The Septuagint Version of the Old Testament, L.C.L. Brenton, 1851, available at <a href='https://ebible.org/eng-Brenton/'>ebible.org</a>"
            ]
        else:
            split_meta_values = unsplit_values
        # After removing HTML and stripping whitespace we are removing duplicates and sorting them.
        cleaned_values = set()
        for v in split_meta_values:
            cleaned_values.add(re.sub(HTML_TAG_REGEX, "", v).strip())
        # Convert to list and sort
        meta_values = sorted(list(cleaned_values))
        return meta_values

    @classmethod
    @cache_memoize(settings.CACHE_TTL)
    def get_value_corpus_pairs(cls, meta):
        value_corpus_pairs = OrderedDict()

        # Directly query the corpora that match the given metadata attribute and its values
        corpora = (
            cls.objects.filter(text_meta__name__iexact=meta["name"])
            .values("corpus__slug", "corpus__title", "corpus__author", "corpus__id", "corpus__urn_code", "corpus__annis_corpus_name", "text_meta__value")
            .order_by("corpus__title")
            .distinct()
        )

        for c in corpora:
            meta_value = c.pop("text_meta__value")
            if meta_value not in value_corpus_pairs:
                value_corpus_pairs[meta_value] = []
            value_corpus_pairs[meta_value].append({key.replace('corpus__', ''): value for key, value in c.items()})

        return OrderedDict(sorted(value_corpus_pairs.items()))

    # FIXME this repeats code in _get_texts
    def get_text(self):
        if  hasattr(self, 'text'):
            return self.text
        else:
            dir_contents, tree_id = self.corpus.repository._get_texts(self.corpus, self.tt_dir)
            self.text=dict(dir_contents).get(self.tt_filename)
            if len(self.text) == 0:
                raise NoTexts(self.corpus.annis_corpus_name, self.corpus.repo_path)
            return self.text

    def get_text_chapters(self):
        # We will have better search results if we return the text as a list of chapters
        # Chapters in the SGML are marked by <chapter_n chapter_n="0">
        # </chapter_n> >
        chapter_pattern = re.compile(r'<chapter_n chapter_n="\d+">(.*?)<\/chapter_n>', re.DOTALL)
        text = self.get_text()
        chapters = {match.group(1) for match in chapter_pattern.finditer(text)}
        if not chapters:
            return [text]
        return chapters

    def get_text_lemmatized(self, text):
        # Text is an SGML document that has been tokenized and lemmatized
        # we want to extract all "lemma" attributes from <norm> tags
        # and contcatenate them into a single string (with spaces)
        # and return that string
        return " ".join(re.findall(r'lemma="([^"]*)"', text))

    def get_text_normalized_group(self, text):
        # we want to extract all "norm" attributes from <norm> tags
        return " ".join(re.findall(r'norm_group="([^"]*)"', text))

    def get_text_normalized(self, text):
        # we want to extract all "norm" attributes from <norm> tags
        return " ".join(re.findall(r'norm="([^"]*)"', text))

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        """On save, update timestamps"""
        if not self.id:
            self.created = datetime.datetime.today()
        self.modified = datetime.datetime.today()
        return super().save(*args, **kwargs)

    def to_json(self):
        json = {
            "title": self.title,
            "slug": self.slug,
            "created": self.created.isoformat(),
            "modified": self.modified.isoformat(),
            "corpus": self.corpus.title if self.corpus else None,
            "corpus_slug": self.corpus.slug if self.corpus else None,
            "text_meta": {},
            "text": [
            {
                "lemmatized": self.get_text_lemmatized(text),
                "normalized": self.get_text_normalized(text),
                "normalized_group": self.get_text_normalized_group(text),
            }
            for text in self.get_text_chapters()
            ],
            "tt_dir": self.tt_dir,
            "tt_filename": self.tt_filename,
            "tt_dir_tree_id": self.tt_dir_tree_id,
            "document_cts_urn": self.document_cts_urn,
        }

        # Process text_meta to handle duplicate keys
        text_meta = self.text_meta.values_list("name", "value")
        meta_dict = {}
        for name, value in text_meta:
            if name in meta_dict.keys():
                # If we encounter a second value for the same key, convert the value to a list
                # We should probably always have an array for splittables.
                meta_dict[name] = [meta_dict[name]]
                meta_dict[name].append(value)
            else:
                meta_dict[name] = value
        json["text_meta"] = meta_dict
        return json
    
    def get_visualization_by_slug(self, format_slug):
        for visualization in self.html_visualizations.all():
            if visualization.visualization_format["slug"] == format_slug:
                return visualization
        raise ValueError(f"Visualization format '{format_slug}' not found for text '{self.title}'")

    # add Full Text Search
    def index(self):
        # Index texts in Meilisearch
        # FIXME this shouldbe done in a seprate command -
        # once we have the text in the database, we can index them.
        search = Search()
        if search.search_available:
            result = search.index_text([self.to_json()])
            logging.info(f"Indexed {self.slug} {result} in full text search.")
        else:
            logging.error("Search is not available.")
            raise "Search not available but trying to index"

    
    @classmethod
    def search(cls, keyword):
        search = Search()
        if search.search_available:
            return search.search(keyword)
        else:
            logger.error("MeiliSearch is not available")
            return {"hits": []}

    # add Full Text Search
    @classmethod
    def faceted_search(cls, keyword):
        search = Search()
        if search.search_available:
            return search.faceted_search(keyword)
        else:
            logger.error("MeiliSearch is not available")
            return {"hits": []}
