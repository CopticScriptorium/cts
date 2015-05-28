"""
expire.py

Expire from their source lists in ANNIS

"""
import pdb
import re
import logging
from urllib import request
from urllib.error import HTTPError
from bs4 import BeautifulSoup
from django.utils.text import slugify
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from xvfbwrapper import Xvfb

def expire_ingest( expire_ingest_instance ):

	"""
	Set all texts is_expired value to true
	"""

	from texts.models import Text

	for text in Text.objects.all():

		text.is_expired = True
		text.save()


def ingest_expired_text( text_id ):


	from texts.models import Text, TextMeta, HtmlVisualization
	from annis.models import AnnisServer

	# Set up an instance of the logger
	logger = logging.getLogger(__name__)

	# Define HTML Formats and the ANNIS server to query 
	annis_server = AnnisServer.objects.all()[:1] 
	vdisplay = Xvfb()
	vdisplay.start()
	driver = webdriver.Firefox()

	if len(annis_server) > 0:
		annis_server = annis_server[0]

		# Ensure trailing slash in the annis server base domain
		if not annis_server.base_domain.endswith("/"):
			annis_server.base_domain += "/"

	else:
		logger.error( "Error with single text re-ingest, no ANNIS server found")
		return False

	# Get the text 
	try:
		text = Text.objects.get( id=text_id )
	except Text.DoesNotExist:
		logger.error( "Error with single text re-ingest, no text found for text id", text_id)
		return False


	# Log the import information
	logger.info(" -- Importing " + text.corpus.title + " " + text.title + " " + str( text.id ) )

	# Query ANNIS for the metadata for the document
	meta_query_url = annis_server.base_domain + annis_server.document_metadata_url.replace(":corpus_name", text.corpus.annis_corpus_name ).replace(":document_name", text.title)
	res = request.urlopen( meta_query_url )
	xml = res.read() 
	soup = BeautifulSoup( xml )
	meta_items = soup.find_all("annotation")

	# Remove old textmeta items
	# And save each meta item for the text document
	text.text_meta.all().delete()
	for meta_item in meta_items:
		text_meta = TextMeta()
		text_meta.name = meta_item.find("name").text
		text_meta.value = meta_item.find("value").text
		text_meta.pre = meta_item.find("pre").text
		meta_corpus_name = meta_item.find("corpusName")
		if meta_corpus_name:
			text_meta.corpus_name = meta_corpus_name.text 
		text_meta.save()
		text.text_meta.add(text_meta)

	# Remove the html visualizations from the text
	# Query ANNIS for each HTML format of the documents
	text.html_visualizations.all().delete()
	for html_format in text.corpus.html_visualization_formats.all():

		# Add the corpus corpus name to the URL
		corpora_url = annis_server.base_domain + annis_server.html_visualization_url.replace(":corpus_name", text.corpus.annis_corpus_name).replace(":document_name", text.title ).replace(":html_visualization_format", html_format.slug)

		# Fetch the HTML for the corpus/document/html_format from ANNIS
		driver.get( corpora_url )

		# Wait for visualization to load in browser
		try:
			element = WebDriverWait(driver, 20).until(
				EC.presence_of_element_located((By.CLASS_NAME, "htmlvis"))
			)
			driver.delete_all_cookies()

			body = driver.find_element_by_xpath("/html/body")
			text_html = body.get_attribute("innerHTML")
			styles = driver.find_elements_by_xpath("/html/head/style")

		except:
			text_html = ""
			styles = []
			driver.quit()
			driver = webdriver.Firefox()

		# Check to ensure there's html returned
		# if "Could not query document" in text_html or "error" in text_html:
		if "Client response status: 403" in text_html:
			logger.error(" -- Error fetching " + corpora_url)
			text_html = ""

		# Remove Javascript from the body content
		if len( text_html ):

			# Add the styles
			for style_elem in styles: 
				style_css = style_elem.get_attribute("innerHTML")
				text_html = text_html + "<style>" + style_css + "</style>"

			# For script element in the html, remove it
			script_elems = re.findall(r'<script.*script>', text_html, re.DOTALL)
			for script_elem in script_elems:
				text_html = text_html.replace( script_elem, "" )

		# Create the new html_visualization
		html_visualization = HtmlVisualization()
		html_visualization.visualization_format = html_format
		html_visualization.html = text_html
		html_visualization.save()

		# Add the html visualization to the text
		text.html_visualizations.add(html_visualization)

	# Save the updated text
	text.is_expired = False 
	text.save()
				
	driver.quit()
	vdisplay.stop()
	return text.id

