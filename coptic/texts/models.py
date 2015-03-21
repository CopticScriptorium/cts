import datetime
from django.db import models
from ingest.models import Ingest
from django.db.models.signals import post_save
import pdb


class Author(models.Model):
	"""
	Model for text authors
	"""

	name = models.CharField(max_length=200)
	urn_code = models.CharField(max_length=200)
	slug = models.SlugField(max_length=40)
	created = models.DateTimeField(editable=False)
	modified = models.DateTimeField(editable=False)

	def __str__(self):
		return self.name

	def save(self, *args, **kwargs):
		''' On save, update timestamps '''
		if not self.id:
			self.created = datetime.datetime.today()
		self.modified = datetime.datetime.today()
		return super(Author, self).save(*args, **kwargs)



class HtmlVisualizationFormat(models.Model):
	"""
	Model for different types of HTML visualizations, such as "norm", "ana", "dipl", and "sahidica"
	"""

	title = models.CharField(max_length=200)
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


class Collection(models.Model):
	"""
	Collection, or also regularized to ANNIS as "Corpus"
	"""

	title = models.CharField(max_length=200)
	urn_code = models.CharField(max_length=200)
	html_corpora_code = models.CharField(max_length=200)
	slug = models.SlugField(max_length=40)
	created = models.DateTimeField(editable=False)
	modified = models.DateTimeField(editable=False)
	annis_code = models.CharField(max_length=200)
	annis_corpus_name = models.CharField(max_length=200)
	author = models.ForeignKey(Author, blank=True, null=True)
	github = models.CharField(max_length=200)
	html_visualization_formats = models.ManyToManyField(HtmlVisualizationFormat, blank=True, null=True)

	def __str__(self):
		return self.title

	def save(self, *args, **kwargs):
		''' On save, update timestamps '''
		if not self.id:
			self.created = datetime.datetime.today()
		self.modified = datetime.datetime.today()
		return super(Collection, self).save(*args, **kwargs)

class TextMeta(models.Model):
	"""
	Meta item ingested from ANNIS	
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

	title = models.CharField(max_length=200)
	slug = models.SlugField(max_length=40)
	created = models.DateTimeField(editable=False)
	modified = models.DateTimeField(editable=False)
	author = models.ForeignKey(Author, blank=True, null=True)
	collection = models.ForeignKey(Collection, blank=True, null=True)
	ingest = models.ForeignKey(Ingest, blank=True, null=True)
	html_visualizations = models.ManyToManyField(HtmlVisualization, blank=True, null=True)
	text_meta = models.ManyToManyField(TextMeta, blank=True, null=True)


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
	annis_name = models.CharField(max_length=200)
	texts_field = models.CharField(max_length=200, blank=True, null=True)
	order = models.IntegerField()
	splittable = models.CharField(max_length=200)

	class Meta:
		verbose_name = "Search Field"

	def __str__(self):
		return self.title

# Search field value
class SearchFieldValue(models.Model):
	"""
	Value for Search Field ingested from Metadata from ANNIS
	"""
	title = models.CharField(max_length=200)
	value = models.CharField(max_length=200)
	search_field = models.ForeignKey(SearchField, blank=True, null=True)
	texts = models.ManyToManyField(Text, blank=True, null=True)

	class Meta:
		verbose_name = "Search Field Value"

	def __str__(self):
		return self.search_field.title  + ": " + self.title 

# Method for performing ingest once there's an ingest.id 
def post_save_search_field(sender, instance, **kwargs):
	''' On save, populate the values field with SeachFieldValues based off the unique values in the texts'''
	populate_values( instance )

# Register the post save signal 
post_save.connect(post_save_search_field, sender=SearchField, dispatch_uid="")	

# Populating values for the search fields
def populate_values( instance ):

	attr = instance.texts_field
	texts = Text.objects.all()
	values = []
	search_field_values = []

	# Select the values for the specified attr in the text
	for text in texts:
		if hasattr( text, attr ):
			value = getattr( text, attr )
			if value not in values:
				values.append( value )
		else:
			print(" -- -- Warning for SearchField:  Text does not have attr", attr, ": Text :", text)


	# Add distinct values for the search field values
	for value in values:

		title = ''
		if hasattr( value, "name" ):
			title = value.name
		elif hasattr( value, "title"):
			title = value.title
		elif hasattr( value, "id"):
			title = value.id
		else:
			title = value 

		is_in_sfvs = False
		for search_field_value in search_field_values:
			if title == search_field_value.title:
				is_in_sfvs = True 

		if not is_in_sfvs:
			sfv = SearchFieldValue()
			sfv.title = title
			sfv.field = instance
			sfv.save()
			search_field_values.append(sfv)

	return True	 

