import logging
from urllib import request
from bs4 import BeautifulSoup
from texts.models import TextMeta, CorpusMeta

logger = logging.getLogger(__name__)


def collect_corpus_meta(url, corpus):
	logger.info("Fetching and saving corpus metadata")
	def factory(): return CorpusMeta()
	collect(url, factory, corpus.corpus_meta)


def collect_text_meta(url, text):
	logger.info("Fetching and saving text metadata")
	def factory(): return TextMeta()
	collect(url, factory, text.text_meta)


def collect(url, factory, parent):
	for fields in get_selected_annotation_fields(url, ('name', 'value', 'pre', 'corpusname')):
		meta = factory()
		meta.name, meta.value, meta.pre, meta.corpus_name = fields
		meta.save()
		parent.add(meta)


def get_selected_annotation_fields(url, field_names):
	'Fetch from the url, and return the requested fields for each annotation found, in a list of lists'
	try:
		soup = BeautifulSoup(request.urlopen(url).read())
		ps = soup.prettify()
		if '(1960)' in ps:
			logger.info(ps)
		annotations = [[a.find(n).text for n in field_names] for a in soup.find_all("annotation")]
		logger.info('Got %d annotations from %s' % (len(annotations), url))
		return annotations
	except Exception as e:
		logger.exception(e)
		return []
