import logging
from urllib import request
from bs4 import BeautifulSoup
from texts.models import TextMeta, CorpusMeta

logger = logging.getLogger(__name__)


def collect_corpus_meta(url, corpus):
	collect(url, CorpusMeta(), corpus.corpus_meta)


def collect_text_meta(url, text):
	collect(url, TextMeta(), text.text_meta)


def collect(url, meta, parent):
	logger.info("Fetching and saving metadata from " + url)
	try:
		res = request.urlopen(url)
		xml = res.read()
		soup = BeautifulSoup( xml )
		meta_items = soup.find_all("annotation")
	except Exception as e:
		logger.error("Error with %s: %s" % (url, e))
		meta_items = []

	for meta_item in meta_items:
		def t(attr_name): return meta_item.find(attr_name).text
		meta.name 		= t('name')
		meta.value 		= t('value')
		meta.pre 		= t('pre')
		meta.corpus_name = t('corpusname')
		meta.save()
		parent.add(meta)
