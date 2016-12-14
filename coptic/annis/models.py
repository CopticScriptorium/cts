import datetime
from django.db.models import Model, DateTimeField, CharField


class AnnisServer(Model):
	created 				= DateTimeField(editable=False)
	modified 				= DateTimeField(editable=False)
	title 					= CharField(max_length=200)
	base_domain 			= CharField(max_length=200)  # https://<host>
	corpus_docname_url 		= CharField(max_length=200)  # <path>/:corpus_name
	document_metadata_url 	= CharField(max_length=200)  # <path>/:corpus_name/:document_name
	html_visualization_url 	= CharField(max_length=200)  # <path>/:corpus_name/:document_name?config=:html_visualization_format

	class Meta:
		verbose_name = "ANNIS Server"
		verbose_name_plural = "ANNIS Servers"

	def __str__(self):
		return self.title

	def save(self, *args, **kwargs):
		''' Update timestamps '''
		if not self.id:
			self.created = datetime.datetime.today()
		self.modified = datetime.datetime.today()

		return super(AnnisServer, self).save(*args, **kwargs)

	def url_corpus_docname(self, corpus_name):
		return self._fill_corpus_url(self.corpus_docname_url, corpus_name)

	def url_document_metadata(self, corpus_name, docname):
		return self._fill_corpus_url(self.document_metadata_url, corpus_name).replace(":document_name", docname)

	def url_html_visualization(self, corpus_name, docname, vis_format):
		return self._fill_corpus_url(self.html_visualization_url, corpus_name).replace(
			":document_name", docname).replace(':html_visualization_format', vis_format)

	def _fill_corpus_url(self, path, corpus_name):
		return self.base_domain + path.replace(":corpus_name", corpus_name)
