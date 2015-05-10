
import datetime
from django.db import models


class AnnisServer(models.Model):
	"""
	Model to configure the ANNIS Server object
	"""

	created = models.DateTimeField(editable=False)
	modified = models.DateTimeField(editable=False)
	title = models.CharField(max_length=200)
	base_domain = models.CharField(max_length=200)
	corpus_metadata_url = models.CharField(max_length=200)
	corpus_docname_url = models.CharField(max_length=200)
	document_metadata_url = models.CharField(max_length=200)
	html_visualization_url = models.CharField(max_length=200)

	class Meta:
		verbose_name = "ANNIS Server"
		verbose_name_plural = "ANNIS Servers"


	def __str__(self):
		return self.title

	def save(self, *args, **kwargs):
		''' On save, update timestamps '''
		if not self.id:
			self.created = datetime.datetime.today()
		self.modified = datetime.datetime.today()

		return super(AnnisServer, self).save(*args, **kwargs)

