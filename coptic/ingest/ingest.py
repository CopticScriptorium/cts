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

	for corpus in Corpus.objects.filter(id__in=(corpora_ids)) if corpora_ids else Corpus.objects.all():
		corpus_name = corpus.annis_corpus_name
		logger.info('Importing corpus ' + corpus.title)
		metadata.collect_corpus_meta(annis_server.url_corpus_metadata(corpus_name), corpus)

		for title, in get_selected_annotation_fields(annis_server.url_corpus_docname(corpus_name), ('name',)):
			slug = slugify(title).__str__()

			# Add exception for besa.letters corpus in ANNIS
			if corpus_name == "besa.letters" and title != corpus.slug:
				continue

			logger.info('Importing title ' + title)

			Text.objects.filter(title=title).delete()

			text = Text()
			text.title = title
			text.slug = slug
			text.save()  # Todo why save here, and again just below?

			metadata.collect_text_meta(annis_server.url_document_metadata(corpus_name, text.title), text)
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
