import datetime
import re
from base64 import b64encode
from django.db import models
from django.core.serializers.json import DjangoJSONEncoder


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


class HtmlVisualizationFormat(models.Model):
    title = models.CharField(max_length=200)
    button_title = models.CharField(max_length=200)
    slug = models.CharField(max_length=200)

    class Meta:
        verbose_name = "HTML Visualization Format"
        verbose_name_plural = "HTML Visualization Formats"
        managed = False  # Tell Django not to create/manage the table

    class Data:
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
    visualization_format_slug = models.CharField(max_length=200)
    html = models.TextField()

    class Meta:
        verbose_name = "HTML Visualization"

    @property
    def visualization_format(self):
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

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        """On save, update timestamps"""
        if not self.id:
            self.created = datetime.datetime.today()
        self.modified = datetime.datetime.today()
        return super().save(*args, **kwargs)


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
