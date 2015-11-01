'Fetch Texts from their source in ANNIS'

from time import sleep
import logging
from django.utils.text import slugify
from selenium import webdriver
from xvfbwrapper import Xvfb
from ingest import search, metadata, visualizations
from ingest.metadata import get_selected_annotation_fields

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

	if annis_server:
		annis_server = annis_server[0]
		if not annis_server.base_domain.endswith("/"):
			annis_server.base_domain += "/"
	else:
		logger.error("No ANNIS server found")
		return False

	ingest = _retry_getting_ingest(ingest_id)
	if not ingest:
		logger.error('Ingest with ID %d not found in database' % ingest_id)
		return

	corpora_ids = ingest.corpora.values_list('id', flat=True)

	logger.info("Starting virtual framebuffer")
	vdisplay = Xvfb()
	try:
		vdisplay.start()
	except Exception as e:
		logger.error('Unable to start Xvfb: %s' % e)
	logger.info("Starting Firefox")
	driver = webdriver.Firefox()

	# For each corpus defined in the database, fetch results from ANNIS
	logger.info("Querying corpora")
	corpora = Corpus.objects.filter(id__in=(corpora_ids)) \
		if corpora_ids else Corpus.objects.all()

	for corpus in corpora:

		def corpus_name_url(part):
			return annis_server.base_domain + part.replace(":corpus_name", corpus.annis_corpus_name)

		metadata.collect_corpus_meta(corpus_name_url(annis_server.corpus_metadata_url), corpus)

		doc_name_query_url = corpus_name_url(annis_server.corpus_docname_url)

		for title, in get_selected_annotation_fields(doc_name_query_url, ('name',)):
			slug = slugify( title ).__str__()

			# Add exception for besa.letters corpus in ANNIS
			if corpus.annis_corpus_name == "besa.letters" and title != corpus.slug:
				continue

			Text.objects.filter(title = title).delete()

			text = Text()
			text.title = title
			text.slug = slug 
			text.save()  # Todo why save here, and again just below?

			logger.info("Importing %s %s %s" % (corpus.title, text.title, text.id))

			# Query ANNIS for the metadata for the document
			meta_query_url = corpus_name_url(annis_server.document_metadata_url).replace(":document_name", text.title)
			metadata.collect_text_meta(meta_query_url, text)

			visualizations.collect(corpus, text, annis_server, driver)

			text.corpus = corpus
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
