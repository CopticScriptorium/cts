import datetime
from base64 import b64encode
from django.db import models


class HtmlVisualizationFormat(models.Model):
	"""
	Model for different types of HTML visualizations, such as "norm", "ana", "dipl", and "sahidica"
	"""

	title = models.CharField(max_length=200)
	button_title = models.CharField(max_length=200)
	slug = models.CharField(max_length=200)

	class Meta:
		verbose_name = "HTML Visualization Format"

	def __str__(self):
		return self.title


class HtmlVisualization(models.Model):
	"""
	HTML Visualization, specifying a format of visualization and the visualization HTML
	"""

	visualization_format = models.ForeignKey(HtmlVisualizationFormat, blank=True, null=True)
	html = models.TextField()

	class Meta:
		verbose_name = "HTML Visualization"

	def __str__(self):
		return self.visualization_format.title


class CorpusMeta(models.Model):
	"""
	Meta corpus item ingested from ANNIS	
	"""

	name = models.CharField(max_length=200)
	value = models.CharField(max_length=200)
	pre = models.CharField(max_length=200)
	corpus_name = models.CharField(max_length=200)

	class Meta:
		verbose_name = "Corpus Meta Item"

	def __str__(self):
		return self.name + ": " + self.value 


class Corpus(models.Model):
	"""
	Corpus model, containing pertinent information to corpora ingested from ANNIS	
	"""

	created = models.DateTimeField(editable=False)
	modified = models.DateTimeField(editable=False)
	title = models.CharField(max_length=200)
	slug = models.SlugField(max_length=40)
	urn_code = models.CharField(max_length=200)
	annis_corpus_name = models.CharField(max_length=200)
	github = models.CharField(max_length=200)
	html_visualization_formats = models.ManyToManyField(HtmlVisualizationFormat, blank=True)
	corpus_meta = models.ManyToManyField(CorpusMeta, blank=True)

	class Meta:
		verbose_name_plural = "Corpora"

	def __str__(self):
		return self.title

	def save(self, *args, **kwargs):
		''' On save, update timestamps '''
		if not self.id:
			self.created = datetime.datetime.today()
		self.modified = datetime.datetime.today()
		return super(Corpus, self).save(*args, **kwargs)

	def annis_corpus_name_b64encoded(self):
		return b64encode(str.encode(self.annis_corpus_name)).decode()


class TextMeta(models.Model):
	"""
	Meta text item ingested from ANNIS	
	"""

	name = models.CharField(max_length=200)
	value = models.CharField(max_length=200)
	pre = models.CharField(max_length=200)
	corpus_name = models.CharField(max_length=200)

	class Meta:
		verbose_name = "Text Meta Item"

	def __str__(self):
		return self.name + ": " + self.value 


class Text(models.Model):
	"""
	Text object for a single document ingested from ANNIS, mapped to many HTML visualizations
	"""

	from ingest.models import Ingest
	title = models.CharField(max_length=200)
	slug = models.SlugField(max_length=40)
	created = models.DateTimeField(editable=False)
	modified = models.DateTimeField(editable=False)
	is_expired = models.BooleanField(default=False)
	corpus = models.ForeignKey(Corpus, blank=True, null=True)
	ingest = models.ForeignKey(Ingest, blank=True, null=True)
	html_visualizations = models.ManyToManyField(HtmlVisualization, blank=True)
	text_meta = models.ManyToManyField(TextMeta, blank=True)


	def __str__(self):
		return self.title

	def save(self, *args, **kwargs):
		''' On save, update timestamps '''
		if not self.id:
			self.created = datetime.datetime.today()
		self.modified = datetime.datetime.today()
		return super(Text, self).save(*args, **kwargs)


class SearchField(models.Model):
	"""
	Search Field ingested from Metadata from ANNIS
	"""

	title = models.CharField(max_length=200)
	order = models.IntegerField()
	splittable = models.CharField(max_length=200, blank=True, null=True)

	class Meta:
		verbose_name = "Search Field"

	def __str__(self):
		return self.title


class SearchFieldValue(models.Model):
	"""
	Value for Search Field ingested from Metadata from ANNIS
	"""
	title = models.CharField(max_length=200)
	search_field = models.ForeignKey(SearchField, blank=True, null=True)
	texts = models.ManyToManyField(Text, blank=True)

	class Meta:
		verbose_name = "Search Field Value"

	def __str__(self):
		return self.search_field.title  + ": " + self.title
