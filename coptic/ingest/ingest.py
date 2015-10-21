'Fetch Texts from their source in ANNIS'

from time import sleep
import logging
from urllib import request
from urllib.error import HTTPError
from bs4 import BeautifulSoup
from django.utils.text import slugify
from selenium import webdriver
from xvfbwrapper import Xvfb
from ingest import search, metadata, visualizations

logger = logging.getLogger(__name__)


def fetch_texts( ingest_id ):
	"""
	For all corpora specified in the database, query the document names and ingest
	specified html visualizations for all document names

	"""

	from texts.models import Corpus, Text, TextMeta, HtmlVisualization
	from annis.models import AnnisServer

	# Define HTML Formats and the ANNIS server to query
	annis_server = AnnisServer.objects.all()[:1] 

	ingest = _retry_getting_ingest(ingest_id)
	if not ingest:
		logger.error('Ingest with ID %d not found in database' % ingest_id)
		return

	corpora_ids = ingest.corpora.values_list('id', flat=True)

	# Delete all former texts, textmeta, and visualizations
	if not corpora_ids:
		logger.info("Deleting all document values")
		Text.objects.all().delete()
		TextMeta.objects.all().delete()
		HtmlVisualization.objects.all().delete()

	logger.info("Starting virtual framebuffer")
	vdisplay = Xvfb()
	try:
		vdisplay.start()
	except Exception as e:
		logger.error('Unable to start Xvfb: %s' % e)
	logger.info("Starting Firefox")
	driver = webdriver.Firefox()

	if len(annis_server) > 0:
		annis_server = annis_server[0]

		# Ensure trailing slash in the annis server base domain
		if not annis_server.base_domain.endswith("/"):
			annis_server.base_domain += "/"

	else:
		logger.error( "Error with ingest, no ANNIS server found")
		return False

	# For each corpus defined in the database, fetch results from ANNIS
	logger.info("Querying corpora")
	corpora = Corpus.objects.filter(id__in=(corpora_ids)) \
		if corpora_ids else Corpus.objects.all()

	for corpus in corpora:

		def make_url_with_corpus_name(part):
			return annis_server.base_domain + part.replace(":corpus_name", corpus.annis_corpus_name)

		metadata.collect_corpus_meta(make_url_with_corpus_name(annis_server.corpus_metadata_url), corpus)

		# Fetch documents based on the docnames specified on the corpus object
		doc_name_query_url = make_url_with_corpus_name(annis_server.corpus_docname_url)

		try:
			res = request.urlopen( doc_name_query_url )
			xml = res.read() 
			soup = BeautifulSoup( xml )
			doc_name_annotations = soup.find_all("annotation")
		except HTTPError:
			logger.error("HTTPError with doc_name_query_url " + doc_name_query_url)
			doc_name_annotations = [] 


		for doc_name in doc_name_annotations:

			# Create a New Text	
			# Text: Title, slug, author, corpus, ingest, xml_tei, xml_paula, html_visualization

			# First, process the slug, and title
			title = doc_name.find("name").text
			slug = slugify( title ).__str__() 

			# Add exception for besa.letters corpus in ANNIS
			if corpus.annis_corpus_name == "besa.letters":
				if title != corpus.slug:
					continue

			# Create a new text
			text = Text()

			# Set the title and slug on the text
			text.title = title
			text.slug = slug 
			text.save()

			logger.info("Importing " + corpus.title + " " + text.title + " " + str(text.id))

			# Query ANNIS for the metadata for the document
			meta_query_url = make_url_with_corpus_name(annis_server.document_metadata_url).replace(":document_name", text.title)
			metadata.collect_text_meta(meta_query_url, text)

			visualizations.collect(corpus, text, title, annis_server, driver)

			# Add the corpus 
			text.corpus = corpus 

			# Add the ingest
			text.ingest = ingest 
			text.save()
				
	driver.quit()
	vdisplay.stop()

	search.process(annis_server)

	logger.info('Finished')

def _retry_getting_ingest(id):
	'This thread is started before the Ingest save is complete. Retry get if needed.'
	from ingest.models import Ingest
	retries_remaining = 10
	ingest_object = None
	while not ingest_object and retries_remaining:
		sleep(1)
		try:
			ingest_object = Ingest.objects.get(id=id)
		except Ingest.DoesNotExist:
			logger.info("Ingest does not (yet) exist")
			retries_remaining -= 1
	return ingest_object
