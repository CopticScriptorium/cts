import logging
from urllib import request
from urllib.error import HTTPError
from bs4 import BeautifulSoup
from texts.models import TextMeta, CorpusMeta

logger = logging.getLogger(__name__)


def collect_corpus_meta(url, corpus):
	def factory(): return CorpusMeta()
	collect(url, factory, corpus.corpus_meta)


def collect_text_meta(url, text):
	def factory(): return TextMeta()
	collect(url, factory, text.text_meta)


def collect(url, factory, parent):
	logger.info("Fetching and saving metadata from " + url)

	for fields in get_selected_annotation_fields(url, ('name', 'value', 'pre', 'corpusname')):
		meta = factory()
		meta.name, meta.value, meta.pre, meta.corpus_name = fields
		meta.save()
		parent.add(meta)


def get_selected_annotation_fields(url, fields):
	'Fetch from the url, and return the requested fields for each annotation found, in a list of lists'
	try:
		soup = BeautifulSoup(request.urlopen(url).read())
		return [[a.find(field).text for field in fields] for a in soup.find_all("annotation")]
	except HTTPError:
		logger.error("HTTPError with " + url)
		return []
