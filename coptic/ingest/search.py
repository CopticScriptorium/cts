import logging
from ingest.metadata import get_selected_annotation_fields

logger = logging.getLogger(__name__)


def process(annis_server):
	from texts.models import SearchField, SearchFieldValue
	from texts.models import Text
	search_fields = _fields(annis_server)
	current_order_and_splittable_by_annis_name = {sf.annis_name:
		{
			'order': 		sf.order,
			'splittable': 	sf.splittable
		}
		for sf in SearchField.objects.all()
	}

	logger.info("Rebuilding %d SearchFields, and SearchFieldValues" % len(search_fields))
	SearchField.objects.all().delete()
	SearchFieldValue.objects.all().delete()

	# Add all new search fields and mappings
	for search_field in search_fields:
		sf = SearchField()
		sf.annis_name = search_field['name']
		sf.title = search_field['name']

		# Preserve any current order and splittable values
		current_order_and_splittable = current_order_and_splittable_by_annis_name.get(sf.annis_name)

		if current_order_and_splittable:
			sf.order 		= current_order_and_splittable['order']
			sf.splittable 	= current_order_and_splittable['splittable']
		else:
			sf.order 		= 10
			sf.splittable 	= ""

		# Save the search field so that it has an id to be added to the
		# search field value search_field foreign key attribute
		sf.save()

		# Save value data
		for value in search_field['values']:
			sfv = SearchFieldValue()
			sfv.search_field = sf
			sfv.value = sfv.title = value['value']
			sfv.save()

			# Search field texts
			for text_id in value['texts']:
				# Add the texts via the native add ManyToMany handling
				for sfv_text in Text.objects.filter(id=text_id):
					sfv.texts.add(sfv_text)

		# Resave the SearchField to apply the search field splittable to the
		# ingested search field values
		sf.save()  # todo understand why (if?) this is necessary


def _fields(annis_server):
	from texts.models import Text

	search_fields = []  # List of dict of 'name', 'values'

	all_texts = Text.objects.all()
	logger.info("Fetching metadata annotations for %d texts" % len(all_texts))

	for text in all_texts:

		meta_query_url = annis_server.base_domain + annis_server.document_metadata_url.replace(
			":corpus_name", text.corpus.annis_corpus_name).replace(":document_name", text.title)
		logger.info("Querying " + text.title + " @ " + meta_query_url)

		for name, value in get_selected_annotation_fields(meta_query_url, ('name', 'value')):

			matching_search_fields = [sf for sf in search_fields if sf['name'] == name]
			if matching_search_fields:
				values_list = matching_search_fields[0]['values']
				matching_values_dicts = [vd for vd in values_list if vd['value'] == value]
				if matching_values_dicts:
					matching_values_dicts[0]['texts'].append(text.id)
				else:
					values_list.append({
						'value': value,
						'texts': [text.id]
					})
			else:
				search_fields.append({
					'name': name,
					'values': [{
						'value': value,
						'texts': [text.id]
					}]
				})

	return search_fields
