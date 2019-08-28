import datetime
import re
from base64 import b64encode
from django.db import models
from .probe_github import github_directory_names


class HtmlVisualizationFormat(models.Model):
	title = models.CharField(max_length=200)
	button_title = models.CharField(max_length=200)
	slug = models.CharField(max_length=200)

	class Meta:
		verbose_name = "HTML Visualization Format"

	def __str__(self):
		return self.title


class HtmlVisualization(models.Model):
	visualization_format = models.ForeignKey(HtmlVisualizationFormat, blank=True, null=True, on_delete=models.CASCADE)
	html = models.TextField()

	class Meta:
		verbose_name = "HTML Visualization"

	def __str__(self):
		return self.visualization_format.title


class Corpus(models.Model):
	created = models.DateTimeField(editable=False)
	modified = models.DateTimeField(editable=False)
	title = models.CharField(max_length=200)
	slug = models.SlugField(max_length=40, db_index=True)
	urn_code = models.CharField(max_length=200, db_index=True)
	annis_corpus_name = models.CharField(max_length=200, db_index=True)
	github          = models.CharField(max_length=200)
	github_tei      = models.CharField(max_length=50, blank=True)
	github_relannis = models.CharField(max_length=50, blank=True)
	github_paula    = models.CharField(max_length=50, blank=True)
	html_visualization_formats = models.ManyToManyField(HtmlVisualizationFormat, blank=True)

	class Meta:
		verbose_name_plural = "Corpora"

	def __str__(self):
		return self.title

	def save(self, *args, **kwargs):
		''' On save, update timestamps '''
		if not self.id:
			self.created = datetime.datetime.today()
		self.modified = datetime.datetime.today()
		self.github_tei, self.github_relannis, self.github_paula = github_directory_names(self)
		super(Corpus, self).save(*args, **kwargs)

	def _annis_corpus_name_b64encoded(self):
		return b64encode(str.encode(self.annis_corpus_name)).decode()

	def annis_link(self):
		return "https://corpling.uis.georgetown.edu/annis/scriptorium#_c=" + self._annis_corpus_name_b64encoded()


class TextMeta(models.Model):
	name  = models.CharField(max_length=200, db_index=True)
	value = models.CharField(max_length=10000, db_index=True)

	class Meta:
		verbose_name = "Text Meta Item"

	def __str__(self):
		return self.name + ": " + self.value

	def value_customized(self):
		v = self.value
		if re.match(r'https?://', v):  # Turn URLs into <a> tags
			return '<a href="%s">%s</a>' % (v, v)

		if v.startswith('urn:cts'):  # Turn cts URNs into <a> tags
			return '<a href="/%s">%s</a>' % (v, v)

		return v


class MetaOrder(models.Model):
	'Metadata names that are ordered ahead of the others when displayed on a text'
	name 		= models.CharField(max_length=200, unique=True)
	order 		= models.IntegerField()

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


	def __str__(self):
		return self.title

	def save(self, *args, **kwargs):
		''' On save, update timestamps '''
		if not self.id:
			self.created = datetime.datetime.today()
		self.modified = datetime.datetime.today()
		return super(Text, self).save(*args, **kwargs)


class SpecialMeta(models.Model):
	'Metadata names that are used to index texts'
	name 		= models.CharField(max_length=200, unique=True)
	order 		= models.IntegerField()
	splittable 	= models.BooleanField(default=False)

	class Meta:
		verbose_name = "Special Metadata Name"

	def __str__(self):
		return self.name
