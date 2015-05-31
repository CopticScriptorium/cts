"""
ingest.py

Fetch Texts from their source in ANNIS

"""
import pdb
import re
from time import sleep
import random
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


def fetch_texts( ingest_id ):
	"""
	For all corpora specified in the database, query the document names and ingest
	specified html visualizations for all document names

	"""

	# Get the text and ingest models (prevent circular import)
	from texts.models import Corpus, Text, CorpusMeta, TextMeta, HtmlVisualization, HtmlVisualizationFormat, SearchField, SearchFieldValue
	from ingest.models import Ingest 
	from annis.models import AnnisServer

	# Set up an instance of the logger
	logger = logging.getLogger(__name__)

	# Delete all former texts, textmeta, and visualizations 
	logger.info(" -- Ingest: Deleting all document values")
	Text.objects.all().delete()
	TextMeta.objects.all().delete()
	HtmlVisualization.objects.all().delete()

	# Define HTML Formats and the ANNIS server to query 
	annis_server = AnnisServer.objects.all()[:1] 

	# Get the Ingest by the ingest id
	ingest = Ingest.objects.get(id=ingest_id)

	logger.info(" -- Ingest: Starting virtual framebuffer")
	vdisplay = Xvfb()
	vdisplay.start()
	logger.info(" -- Ingest: Starting Firefox")
	driver = webdriver.Firefox()

	if len(annis_server) > 0:
		annis_server = annis_server[0]

		# Ensure trailing slash in the annis server base domain
		if not annis_server.base_domain.endswith("/"):
			annis_server.base_domain += "/"

	else:
		logger.error( "Error with ingest, no ANNIS server found")
		return False

	#
	# This is where the corpus ingest from ANNIS should be built out
	#
	# corpus_name_query_url = annis_server.base_domain + annis_server.
	# res = request.urlopen( doc_name_query_url )
	# xml = res.read() 

	# soup = BeautifulSoup( xml )
	# doc_name_annotations = soup.find_all("annotation")

	# For each corpus defined in the database, fetch results from ANNIS
	logger.info(" -- Ingest: querying corpora")
	for corpus in Corpus.objects.all():

		# Query ANNIS for the metadata for the corpus
		meta_query_url = annis_server.base_domain + annis_server.corpus_metadata_url.replace(":corpus_name", corpus.annis_corpus_name )
		try:
			res = request.urlopen( meta_query_url )
			xml = res.read() 
			soup = BeautifulSoup( xml )
			meta_items = soup.find_all("annotation")
		except HTTPError:
			logger.error(" -- Ingest: HTTPError with meta_query_url " + meta_query_url)
			meta_items = [] 

		# Save each meta item for the text document
		for meta_item in meta_items:
			corpus_meta = CorpusMeta()
			corpus_meta.name = meta_item.find("name").text
			corpus_meta.value = meta_item.find("value").text
			corpus_meta.pre = meta_item.find("pre").text
			meta_corpus_name = meta_item.find("corpusName")
			if meta_corpus_name:
				corpus_meta.corpus_name = meta_corpus_name.text 
			corpus_meta.save()
			corpus.corpus_meta.add(corpus_meta)

		# Fetch documents based on the docnames specified on the corpus object
		doc_name_query_url = annis_server.base_domain + annis_server.corpus_docname_url.replace(":corpus_name", corpus.annis_corpus_name)

		try:
			res = request.urlopen( doc_name_query_url )
			xml = res.read() 
			soup = BeautifulSoup( xml )
			doc_name_annotations = soup.find_all("annotation")
		except HTTPError:
			logger.error(" -- Ingest: HTTPError with meta_query_url " + meta_query_url)
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

			logger.info(" -- Importing " + corpus.title + " " + text.title + " " + str( text.id ) )

			# Query ANNIS for the metadata for the document
			meta_query_url = annis_server.base_domain + annis_server.document_metadata_url.replace(":corpus_name", corpus.annis_corpus_name ).replace(":document_name", text.title)
			res = request.urlopen( meta_query_url )
			xml = res.read() 
			soup = BeautifulSoup( xml )
			meta_items = soup.find_all("annotation")

			# Save each meta item for the text document
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


			# Query ANNIS for each HTML format of the documents
			for html_format in corpus.html_visualization_formats.all():

				# Add the corpus corpus name to the URL
				corpora_url = annis_server.base_domain + annis_server.html_visualization_url.replace(":corpus_name", corpus.annis_corpus_name).replace(":document_name", doc_name.find("name").text ).replace(":html_visualization_format", html_format.slug)

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


			# Add the corpus 
			text.corpus = corpus 

			# Add the ingest
			text.ingest = ingest 
			text.save()
				
	driver.quit()
	vdisplay.stop()

	#
	# Then query ANNIS for text meta values and document metadata
	#
	# Define meta_xml list and the ANNIS server to query 
	search_fields = []

	# For each text defined in the database, fetch results from ANNIS
	for text in Text.objects.all():

		# Add the text name to the URL
		meta_query_url = annis_server.base_domain + annis_server.document_metadata_url.replace(":corpus_name", text.corpus.annis_corpus_name ).replace(":document_name", text.title)
		logger.info(" -- Ingest: querying " + text.title + " @ " + meta_query_url)

		# Fetch the HTML for the corpus/document/html_format from ANNIS
		try:
			res = request.urlopen( meta_query_url )
			xml = res.read() 
			soup = BeautifulSoup( xml )
			annotations = soup.find_all("annotation")
		except HTTPError:
			logger.error(" -- Ingest: HTTPError with meta_query_url " + meta_query_url)
			annotations = [] 

		for annotation in annotations:
			name = annotation.find("name").text
			value = annotation.find("value").text

			is_in_search_fields = False
			for search_field in search_fields:
				if search_field['name'] == name:
					is_in_search_fields = True

					is_in_search_field_texts = False
					for sfc in search_field['values']:
						if value == sfc['value']:
							is_in_search_field_texts = True
							sfc['texts'].append(text.id)

					if not is_in_search_field_texts:
						search_field['values'].append({
								'value' : value,
								'texts' : [text.id]
							})


			if not is_in_search_fields:
				search_fields.append({
						'name' : name,
						'values' : [{
								'value' : value,
								'texts' : [text.id]
							}]
					})

	# Make a shadow copy of all Search Fields
	original_search_fields = []
	for sf in SearchField.objects.all():
		original_search_fields.append({
				'title' : sf.title,
				'annis_name' : sf.annis_name,
				'order' : sf.order,
				'splittable' : sf.splittable
			})	

	# And delete all former searchfield values
	logger.info(" -- Ingest: Deleting all SearchFields and SearchFieldValues")
	SearchField.objects.all().delete()
	SearchFieldValue.objects.all().delete()

	# Add all new search fields and mappings
	logger.info(" -- Ingest: Ingesting new SearchFields and SearchFieldValues")
	for search_field in search_fields:
		sf = SearchField()
		sf.annis_name = search_field['name']
		sf.title = search_field['name']

		# Check the search fields against the original search fields
		# If there is a match in the original search fields, take the 
		# order and splittable values from the original search fields
		matched_original_searchfield = False
		original_search_field = {}
		for orig_sf in original_search_fields:
			if sf.annis_name == orig_sf['annis_name']:
				matched_original_searchfield = True
				original_search_field = orig_sf


		if matched_original_searchfield:
			sf.order = original_search_field['order']
			sf.splittable = original_search_field['splittable']

		else:
			sf.order = 10 
			sf.splittable = ""

		# Save the search field so that it has an id to be added to the 
		# search field value search_field foreign key attribute 
		sf.save()

		# Save value data
		for value in search_field['values']:

			sfv = SearchFieldValue()
			sfv.search_field = sf
			sfv.value = value['value']
			sfv.title = value['value']
			sfv.save()

			# Search field texts
			for text_id in value['texts']:

				sfv_texts = Text.objects.filter(id=text_id)

				# Add the texts via the native add ManyToMany handling
				if len( sfv_texts ):
					for sfv_text in sfv_texts: 
						sfv.texts.add( sfv_text )

		# Resave the SearchField to apply the search field splittable to the
		# ingested search field values 
		sf.save()
