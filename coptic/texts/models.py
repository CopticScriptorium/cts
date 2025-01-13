import datetime
import os
import re
import logging
from collections import OrderedDict
from base64 import b64encode
from django.db import models
from django.conf import settings
from cache_memoize import cache_memoize

from texts.ft_search import Search
from gh_ingest.htmlvis import generate_visualization
from gh_ingest.scraper_exceptions import NoTexts, TTDirMissing
from gh_ingest.repository import Repository

# Configure logger
logger = logging.getLogger(__name__)

HTML_TAG_REGEX = re.compile(r"<[^>]*?>")

@cache_memoize(settings.CACHE_TTL)
def get_meta_values(meta):
    unsplit_values = map(
        lambda x: x["value"],
        TextMeta.objects.filter(name__iexact=meta.name)
        .values("value")
        .distinct(),
    )
    if not meta.splittable:
        meta_values = unsplit_values
    else:
        sep = "; " if str(meta.name) in ["places", "people"] else ", "
        split_meta_values = [v.split(sep) for v in unsplit_values]
        for i, vals in enumerate(split_meta_values):
            if (
                any(len(v) > 50 for v in vals) and sep == ", "
            ):  # e.g. long translation value with comma somewhere
                split_meta_values[i] = [", ".join(vals)]
        meta_values = set()
        for vals in split_meta_values:
            meta_values = meta_values.union(set(vals))
    meta_values = sorted(list({v.strip() for v in meta_values}))
    meta_values = [re.sub(HTML_TAG_REGEX, "", meta_value) for meta_value in meta_values]
    #logger.debug("Meta Values: %s", meta_values)  # Debug statement
    return meta_values


class HtmlVisualizationFormatManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().none()

    def _create_object_from_params(self, params):
        instance = HtmlVisualizationFormat(**params)
        instance._state.adding = False
        instance._state.db = "default"
        instance.id = hash(instance.slug)
        return instance

    def all(self):
        return [
            self._create_object_from_params(data)
            for data in HtmlVisualizationFormat.Data.FORMATS.values()
        ]

    def values_list(self, field_name, flat=False):
        all_objects = self.all()
        if flat:
            return [getattr(obj, field_name) for obj in all_objects]
        return [(getattr(obj, field_name),) for obj in all_objects]

    def get(self, **kwargs):
        formats = {
            data["slug"]: self._create_object_from_params(data)
            for data in HtmlVisualizationFormat.Data.FORMATS.values()
        }

        if "slug" in kwargs:
            return formats.get(kwargs["slug"])
        if "button_title" in kwargs:
            return next(
                (
                    f
                    for f in formats.values()
                    if f.button_title == kwargs["button_title"]
                ),
                None,
            )

        raise HtmlVisualizationFormat.DoesNotExist

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
    visualization_formats = models.TextField(default="")

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
        self.visualization_formats = ",".join(f.slug for f in formats)

    @property
    def html_visualization_formats(self):
        """Return HtmlVisualizationFormat objects in the stored order."""
        return [
            HtmlVisualizationFormat.objects.get(slug=slug)
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

class HtmlVisualizationFormat(models.Model):
    title = models.CharField(max_length=200)
    button_title = models.CharField(max_length=200)
    slug = models.CharField(max_length=200)

    class Meta:
        verbose_name = "HTML Visualization Format"
        verbose_name_plural = "HTML Visualization Formats"
        managed = False  # Tell Django not to create/manage the table

    class Data:
        # FIXME: I'd actually like to refactor this and
        # get rid of 
        # norm/norm/normalized -> normalized
        # dipl/dipl/diplomatic -> diplomatic
        # sahidica/sahidica/chapter -> sahidica? - maybe sahidica_chapter?
        # versified/verses/versified -> versified
        FORMATS = OrderedDict([
            ("norm", dict(slug="norm", button_title="normalized", title="Normalized Text")),
            ("analytic", dict(slug="analytic", button_title="analytic", title="Analytic Visualization")),
            ("dipl", dict(slug="dipl", button_title="diplomatic", title="Diplomatic Edition")),
            ("sahidica", dict(slug="sahidica", button_title="chapter", title="Sahidica Chapter View")),
            ("versified", dict(slug="verses", button_title="versified", title="Versified Text")),
        ])

    objects = HtmlVisualizationFormatManager()

    def __str__(self):
        return self.title  # Changed from self.visualization_format.title to self.title


class HtmlVisualization(models.Model):
    #FIXME this model is probably not needed at all ..
    # get_html_visualization should be a method on Text
    visualization_format_slug = models.CharField(max_length=200)
    html = models.TextField()

    class Meta:
        verbose_name = "HTML Visualization"

    @property
    def html_live(self):
        tt_text = self.text_set.get().get_text()
        return generate_visualization(self.visualization_format_slug, tt_text)
    
    
    @property
    def visualization_format(self):
        # FIXME: this probably wants to be cached - and possibly
        # shared - I don't think it is ever different
        return HtmlVisualizationFormat.objects.get(slug=self.visualization_format_slug)

    @visualization_format.setter
    def visualization_format(self, format_obj):
        """Set the visualization format using a HtmlVisualizationFormat object"""
        if format_obj is None:
            self.visualization_format_slug = None
        else:
            self.visualization_format_slug = format_obj.slug

    def __str__(self):
        return self.visualization_format.title


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


class MetaOrder(models.Model):
    "Metadata names that are ordered ahead of the others when displayed on a text"
    name = models.CharField(max_length=200, unique=True)
    order = models.IntegerField()

    class Meta:
        verbose_name = "Metadata Order"

    def __str__(self):
        return self.name

class Text(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=40, db_index=True)
    created = models.DateTimeField(editable=False)
    modified = models.DateTimeField(editable=False)
    corpus = models.ForeignKey(Corpus, blank=True, null=True, on_delete=models.CASCADE)
    html_visualizations = models.ManyToManyField(HtmlVisualization, blank=True)
    text_meta = models.ManyToManyField(TextMeta, blank=True, db_index=True)
    tt_dir = models.CharField(max_length=40)
    tt_filename = models.CharField(max_length=40)
    tt_dir_tree_id = models.CharField(max_length=40)
    document_cts_urn = models.CharField(max_length=80)

    @classmethod
    @cache_memoize(settings.CACHE_TTL)
    def get_value_corpus_pairs(cls, meta):
        value_corpus_pairs = OrderedDict()
        meta_values = get_meta_values(meta)

        corpora = (
            cls.objects.filter(text_meta__name__iexact=meta.name, text_meta__value__in=meta_values)
            .values("corpus__slug", "corpus__title", "corpus__id", "corpus__urn_code", "corpus__annis_corpus_name", "text_meta__value")
            .order_by("corpus__title")
            .distinct()
        )

        for c in corpora:
            meta_value = c.pop("text_meta__value")
            c["corpus__author"]=', '.join(list(cls.objects.filter(corpus_id = c["corpus__id"],text_meta__name__iexact="author").values_list("text_meta__value", flat=True).distinct()))
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
    
    def get_text_lemmatized(self):
        # Text is an SGML document that has been tokenized and lemmatized
        # we want to extract all "lemma" attributes from <norm> tags
        # and contcatenate them into a single string (with spaces)
        # and return that string
        return " ".join(re.findall(r'lemma="([^"]*)"', self.get_text()))

    def get_text_normalized(self):
        # Text is an SGML document that has been tokenized and lemmatized
        # we want to extract all "norm" attributes from <norm> tags
        # and contcatenate them into a single string (with spaces)
        # and return that string
        return " ".join(re.findall(r'norm="([^"]*)"', self.get_text()))
    
    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        """On save, update timestamps"""
        if not self.id:
            self.created = datetime.datetime.today()
        self.modified = datetime.datetime.today()
        return super().save(*args, **kwargs)
        
    def to_json(self):
        return {
            "id": self.id,
            "title": self.title,
            "slug": self.slug,
            "created": self.created.isoformat(),
            "modified": self.modified.isoformat(),
            "corpus": self.corpus.title if self.corpus else None,
            "corpus_slug": self.corpus.slug if self.corpus else None,
            "text_meta": {meta.name: meta.value for meta in self.text_meta.all()},
            "text": [
                {
                    "lemmatized": self.get_text_lemmatized(),
                    "normalized": self.get_text_normalized(),
                }
                for vis in self.html_visualizations.all()
            ],
            "tt_dir": self.tt_dir,
            "tt_filename": self.tt_filename,
            "tt_dir_tree_id": self.tt_dir_tree_id,
            "document_cts_urn": self.document_cts_urn,
        }


    def get_visualization_by_slug(self, format_slug):
        for visualization in self.html_visualizations.all():
            print(visualization)
            print(visualization.visualization_format.slug )
            if visualization.visualization_format.slug == format_slug:
                return visualization
        raise ValueError(f"Visualization format '{format_slug}' not found for text '{self.title}'")

    #add Full Text Search
    @classmethod
    def search(cls, keyword):
        search = Search()
        if search.search_available:
            return search.search(keyword)
        else:
            logger.error("MeiliSearch is not available")
            return {"hits": []}


class SpecialMetaManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().none()

    def order_by(self, *fields):
        objects = self.all()
        for field in reversed(fields):
            desc = False
            if field.startswith("-"):
                desc = True
                field = field[1:]

            if field.startswith('Lower("'):
                field = field[7:-2]  # Extract field name from Lower("field")

            objects = sorted(
                objects, key=lambda x: getattr(x, field).lower(), reverse=desc
            )
        return objects

    def _create_object_from_params(self, params):
        instance = SpecialMeta(**params)
        instance._state.adding = False
        instance._state.db = "default"
        instance.id = hash(instance.name)
        return instance

    def all(self):
        return [
            self._create_object_from_params(params)
            for params in SpecialMeta.Data.METAS.values()
        ]

    def get(self, **kwargs):
        all_objects = self.all()
        if "name" in kwargs:
            try:
                return next(obj for obj in all_objects if obj.name == kwargs["name"])
            except StopIteration:
                raise SpecialMeta.DoesNotExist()
        raise ValueError("get() must be called with 'name'")

    def values_list(self, field_name, flat=False):
        all_objects = self.all()
        if flat:
            return [getattr(obj, field_name) for obj in all_objects]
        return [(getattr(obj, field_name),) for obj in all_objects]


class SpecialMeta(models.Model):
    name = models.CharField(max_length=200, unique=True)
    order = models.IntegerField()
    splittable = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Special Metadata Name"
        managed = False

    class Data:
        METAS = {
            "corpus": dict(name="corpus", order=1, splittable=False),
            "author": dict(name="author", order=2, splittable=False),
            "people": dict(name="people", order=3, splittable=True),
            "places": dict(name="places", order=4, splittable=True),
            "ms_name": dict(name="msName", order=5, splittable=False),
            "annotation": dict(name="annotation", order=6, splittable=True),
            "translation": dict(name="translation", order=7, splittable=True),
            "arabic_translation": dict(
                name="arabic_translation", order=8, splittable=True
            ),
        }

    objects = SpecialMetaManager()

    def __str__(self):
        return self.name
