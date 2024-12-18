import datetime
import os
import re
import logging
from base64 import b64encode
from django.db import models
import base64
from collections import OrderedDict
from coptic.settings.base import HTML_CONFIGS
from gh_ingest.htmlvis import generate_visualization
from gh_ingest.scraper_exceptions import NoTexts, TTDirMissing
# Configure logger
logger = logging.getLogger(__name__)

HTML_TAG_REGEX = re.compile(r"<[^>]*?>")

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

    def get_text(self, corpus, tt_dir,tt_filename):
        corpus_path = os.path.join("../../corpora",tt_dir, corpus.annis_corpus_name+"_TT")
        text = ""

        try:
            if corpus.github_relannis.endswith("zip"):
                dir_contents = self._get_all_files_in_zip(corpus_path + ".zip")
                text = next(contents for name, contents in dir_contents if name == tt_filename)
            else:
                with open(os.path.join(corpus_path, tt_filename)) as file:
                    text = file.read()
        except FileNotFoundError as e:
            raise TTDirMissing(os.path.join(corpus_path, tt_filename)) from e

        if len(text) == 0:
            raise NoTexts(corpus.annis_corpus_name, self.local_repo_path)

        return text

    @property
    def html_live(self):
        # FIXME: we can probably refactor
        # this to something like a dict or
        # a template? Anyway the weird TSV
        # is weird.
    
        text = self.text_set.all()
        tt_dir, tt_filename = list(self.text_set.values_list('tt_dir','tt_filename'))[0]
        corpus = text.values("corpus")[0]["corpus"]
        tt_text = self.get_text(Corpus.objects.get(id=corpus),tt_dir, tt_filename)
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
    slug = models.SlugField(max_length=40, db_index=True) #Fixme: making the slug unique seems to fail import.
    created = models.DateTimeField(editable=False)
    modified = models.DateTimeField(editable=False)
    corpus = models.ForeignKey(Corpus, blank=True, null=True, on_delete=models.CASCADE)
    html_visualizations = models.ManyToManyField(HtmlVisualization, blank=True)
    text_meta = models.ManyToManyField(TextMeta, blank=True, db_index=True)
    title = models.CharField(max_length=200)
    tt_dir = models.CharField(max_length=40)
    tt_filename = models.CharField(max_length=40)
    tt_dir_tree_id = models.CharField(max_length=40)
    document_cts_urn= models.CharField(max_length=80)
    
    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        """On save, update timestamps"""
        if not self.id:
            self.created = datetime.datetime.today()
        self.modified = datetime.datetime.today()
        return super().save(*args, **kwargs)

    def get_visualization_by_slug(self, format_slug):
        for visualization in self.html_visualizations.all():
            print(visualization)
            print(visualization.visualization_format.slug )
            if visualization.visualization_format.slug == format_slug:
                return visualization
        raise ValueError(f"Visualization format '{format_slug}' not found for text '{self.title}'")

    @classmethod
    def get_authors_for_corpus(cls, corpus_id):
        authors = TextMeta.objects.filter(
            text__corpus__id=corpus_id,
            name__iexact="author"
        ).values_list('value', flat=True).distinct()
        authors_set = set(authors)
        logger.debug("Authors for Corpus: %s", authors_set)  # Debug statement
        return authors_set

    @classmethod
    def get_corpora_for_meta_value(cls, meta_name, meta_value, splittable):
        if splittable:
            corpora = (
                cls.objects.filter(
                    text_meta__name__iexact=meta_name,
                    text_meta__value__icontains=meta_value,
                )
                .values(
                    "corpus__slug",
                    "corpus__title",
                    "corpus__id",
                    "corpus__urn_code",
                    "corpus__annis_corpus_name",
                )
                .distinct()
            )
        else:
            corpora = (
                cls.objects.filter(
                    text_meta__name__iexact=meta_name,
                    text_meta__value__iexact=meta_value,
                )
                .values(
                    "corpus__slug",
                    "corpus__title",
                    "corpus__id",
                    "corpus__urn_code",
                    "corpus__annis_corpus_name",
                )
                .distinct()
            )
        #logger.debug("Corpora for Meta Value: %s", corpora)  # Debug statement
        return corpora

    @classmethod
    def get_value_corpus_pairs(cls, meta):
        meta_values = get_meta_values(meta)
        value_corpus_pairs = OrderedDict()

        for meta_value in meta_values:
            corpora = cls.get_corpora_for_meta_value(meta.name, meta_value, meta.splittable)
            value_corpus_pairs[meta_value] = []

            for c in sorted(corpora, key=lambda x: x["corpus__title"]):
                authors = cls.get_authors_for_corpus(c["corpus__id"])
                # FIXME: This is really weird logic.
                # We have 0 authors, 1 author, 2 authors, 3+ authors
                # Ordering may be important in the case of 2 authors
                # but we don't have that information here?
                # Possibly authors may come from two distinct fields?
                # attributed_author and author ? But we are not using that here.
                if len(authors) == 0:
                    author = None
                elif len(authors) == 1:
                    author = list(authors)[0]
                elif len(authors) < 3:
                    author = ", ".join(authors)
                else:
                    author = "multiple"

                value_corpus_pairs[meta_value].append(
                    {
                        "slug": c["corpus__slug"],
                        "title": c["corpus__title"],
                        "urn_code": c["corpus__urn_code"],
                        "author": author,
                        "annis_corpus_name": c["corpus__annis_corpus_name"],
                    }
                )
            value_corpus_pairs[meta_value].sort(key=lambda x: x["title"])

        logger.debug("Value Corpus Pairs: %s", value_corpus_pairs)  # Debug statement
        return value_corpus_pairs

    @classmethod
    def get_b64_meta_values(cls, value_corpus_pairs):
        return {
            meta_value: str(base64.b64encode(('identity="' + meta_value + '"').encode("ascii")).decode("ascii"))
            for meta_value in value_corpus_pairs.keys()
        }

    @classmethod
    def get_b64_corpora(cls, value_corpus_pairs):
        for meta_value in value_corpus_pairs.values():
            for c in meta_value:
                if "annis_corpus_name" not in c:
                    logger.debug("Missing key in: %s", c)
                else:
                    logger.debug("Key found in: %s", c)
        return {
            c["annis_corpus_name"]: str(base64.b64encode(c["annis_corpus_name"].encode("ascii")).decode("ascii"))
            for meta_value in value_corpus_pairs.values()
            for c in meta_value
        }

    @classmethod
    def get_all_corpora(cls, value_corpus_pairs):
        return {c["annis_corpus_name"] for meta_value in value_corpus_pairs.values() for c in meta_value}


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
