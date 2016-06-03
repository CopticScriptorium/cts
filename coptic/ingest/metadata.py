import logging
import requests
from bs4 import BeautifulSoup
from texts.models import TextMeta, CorpusMeta

logger = logging.getLogger(__name__)


def collect_corpus_meta(url, corpus):
	logger.info("Fetching and saving corpus metadata")
	collect(url, CorpusMeta, corpus.corpus_meta)


def collect_text_meta(url, text):
	logger.info("Fetching and saving text metadata")
	def factory(): return TextMeta()
	collect(url, TextMeta, text.text_meta)


def collect(url, table, parent):
	parent.remove()
	all_meta = list(table.objects.all())
	for name, value in get_selected_annotation_fields(url, ('name', 'value')):
		existing = [item for item in all_meta if item.name == name and item.value == value]
		if existing:
			if len(existing) > 1:
				logger.info('There are %d duplicates for %s: %s.' % (len(existing) - 1, name, value))
			meta = existing[0]
		else:
			meta = table()
			meta.name, meta.value = name, value
			meta.save()
		parent.add(meta)


def get_selected_annotation_fields(url, field_names):
	'Fetch from the url, and return the requested fields for each annotation found, in a list of lists'
	try:
		response = requests.get(url)
		content = response.content
		soup = BeautifulSoup(content, from_encoding='utf-8')
		annotations = soup.find_all("annotation")
		annotation_sets = [[a.find(n).text for n in field_names] for a in annotations]
		logger.info('Got %d annotation sets from %s' % (len(annotation_sets), url))
		return annotation_sets
	except Exception as e:
		logger.exception(e)
		return []
