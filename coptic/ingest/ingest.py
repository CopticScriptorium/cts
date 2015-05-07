"""
ingest.py

Fetch Texts from their source lists in ANNIS

"""
import re
from urllib import request
from urllib.error import HTTPError
from bs4 import BeautifulSoup
from selenium import webdriver
from django.utils.text import slugify
from time import sleep
import random

def fetch_texts( ingest ):
	"""
	For all corpora specified in the database, query the document names and ingest
	specified html visualizations for all document names

	"""

	# Get the text and ingest models (prevent circular import)
	from texts.models import Corpus, Text, TextMeta, HtmlVisualization, HtmlVisualizationFormat, SearchField, SearchFieldValue
	from ingest.models import Ingest 
	from annis.models import AnnisServer

	# Delete all former texts, textmeta, and visualizations 
	print(" -- Ingest: Deleting all document values")
	Text.objects.all().delete()
	TextMeta.objects.all().delete()
	HtmlVisualization.objects.all().delete()

	# Delete all former searchfield values
	print(" -- Ingest: Deleting all SearchFields and SearchFieldValues")
	SearchField.objects.all().delete()
	SearchFieldValue.objects.all().delete()

	# Define HTML Formats and the ANNIS server to query 
	annis_server = AnnisServer.objects.all()[:1] 
	driver = webdriver.Firefox()

	if len(annis_server) > 0:
		annis_server = annis_server[0]
	else:
		print( "Error with ingest, no ANNIS server found")
		return False

	# For each corpus defined in the database, fetch results from ANNIS
	for corpus in Corpus.objects.all():

		# Fetch documents based on the docnames specified on the corpus object
		doc_name_query_url = "http://corpling.uis.georgetown.edu/annis-service/annis/meta/docnames/" + corpus.annis_corpus_name
		res = request.urlopen( doc_name_query_url )
		xml = res.read() 

		soup = BeautifulSoup( xml )
		doc_name_annotations = soup.find_all("annotation")

		for doc_name in doc_name_annotations:

			# Create a New Text	
			# Text: Title, slug, author, corpus, ingest, xml_tei, xml_paula, html_visualization

			# First, process the slug, and title
			title = doc_name.find("name").text
			slug = slugify( title ).__str__() 

			# Create a new text
			text = Text()

			# Set the title and slug on the text
			text.title = title
			text.slug = slug 
			text.save()

			print(" -- Importing", corpus.title, text.title, text.id)


			# Query ANNIS for the metadata for the document
			meta_query_url = "http://corpling.uis.georgetown.edu/annis-service/annis/meta/doc/" + corpus.annis_corpus_name + "/" + title
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
				corpora_url = annis_server.html_url + corpus.annis_corpus_name

				# Add the document name to the corpora URL
				corpora_url = corpora_url + "/" + doc_name.find("name").text

				# Add the html format to the corpora URL
				corpora_url = corpora_url + "?config=" + html_format.slug + "&v-1425855020142"

				# Fetch the HTML for the corpus/document/html_format from ANNIS
				driver.get( corpora_url )
				sleep( random.randint( 11,13 ) )
				driver.delete_all_cookies()

				body = driver.find_element_by_xpath("/html/body")
				text_html = body.get_attribute("innerHTML")
				styles = driver.find_elements_by_xpath("/html/head/style")

				# Check to ensure there's html returned
				# if "Could not query document" in text_html or "error" in text_html:
				if "Client response status: 403" in text_html:
					print(" -- Error fetching", corpora_url)
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

	#
	# Then query ANNIS for text meta values and document metadata
	#
	# Define meta_xml list and the ANNIS server to query 
	search_fields = []
	annis_server = AnnisServer.objects.all()[:1] 

	# Ensure there is an annis server available to query
	if len(annis_server) > 0:
		annis_server = annis_server[0]
	else:
		print( "Error with ingest, no ANNIS server found")
		return False

	# For each text defined in the database, fetch results from ANNIS
	for text in Text.objects.all():

		# Add the text name to the URL
		corpora_url = "http://corpling.uis.georgetown.edu/annis-service/annis/meta/doc/" + text.corpus.annis_corpus_name + "/" + text.title
		print(" -- Ingest: querying", text.title)

		# Fetch the HTML for the corpus/document/html_format from ANNIS
		try:
			res = request.urlopen( corpora_url )
			xml = res.read() 
			soup = BeautifulSoup( xml )
			annotations = soup.find_all("annotation")
		except HTTPError:
			print(" -- Ingest: HTTPError with corpora_url", corpora_url)
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
							sfc['texts'].append(text.slug)

					if not is_in_search_field_texts:
						search_field['values'].append({
								'value' : value,
								'texts' : [text.slug]
							})


			if not is_in_search_fields:
				search_fields.append({
						'name' : name,
						'values' : [{
								'value' : value,
								'texts' : [text.slug]
							}]
					})

		sleep(1)


	# Add all new search fields and mappings
	print(" -- Ingest: Ingesting new SearchFields and SearchFieldValues")
	for search_field in search_fields:
		sf = SearchField()
		sf.annis_name = search_field['name']
		sf.title = search_field['name']
		sf.order = 10 
		sf.save()

		# Save value data
		for value in search_field['values']:

			sfv = SearchFieldValue()
			sfv.search_field = sf
			sfv.value = value['value']
			sfv.title = value['value']
			sfv.save()

			# Search field texts
			for text in value['texts']:

				sfv_texts = Text.objects.filter(slug=text)

				# Add the texts via the native add ManyToMany handling
				if len( sfv_texts ):
					for sfv_text in sfv_texts: 
						sfv.texts.add( sfv_text )

