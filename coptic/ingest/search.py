import logging
from urllib import request
from urllib.error import HTTPError
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


def process(annis_server):
	from texts.models import SearchField, SearchFieldValue
	from texts.models import Text
	search_fields = _fields(annis_server)
	original_search_fields = _database_search_fields()

	# todo merge rather than delete?
	# logger.info("Deleting all SearchFields and SearchFieldValues")
	# SearchField.objects.all().delete()
	# SearchFieldValue.objects.all().delete()

	# Add all new search fields and mappings
	logger.info("Ingesting new SearchFields and SearchFieldValues")
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


def _fields(annis_server):
	from texts.models import Text

	search_fields = []

	# For each text defined in the database, fetch results from ANNIS
	for text in Text.objects.all():

		# Add the text name to the URL
		meta_query_url = annis_server.base_domain + annis_server.document_metadata_url.replace(
			":corpus_name", text.corpus.annis_corpus_name ).replace(":document_name", text.title)
		logger.info("querying " + text.title + " @ " + meta_query_url)

		# Fetch the HTML for the corpus/document/html_format from ANNIS
		try:
			res = request.urlopen( meta_query_url )
			xml = res.read()
			soup = BeautifulSoup( xml )
			annotations = soup.find_all("annotation")
		except HTTPError:
			logger.error("HTTPError with meta_query_url " + meta_query_url)
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

	return search_fields

def _database_search_fields():
	from texts.models import SearchField

	original_search_fields = []

	for sf in SearchField.objects.all():
		original_search_fields.append({
				'title' : sf.title,
				'annis_name' : sf.annis_name,
				'order' : sf.order,
				'splittable' : sf.splittable
			})

	return original_search_fields