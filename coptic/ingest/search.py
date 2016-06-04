import logging
from ingest.metadata import get_selected_annotation_fields
from texts.models import Corpus

logger = logging.getLogger(__name__)


def process(annis_server):
	from texts.models import SpecialMeta, SearchField, SearchFieldValue
	from texts.models import Text
	search_fields = _fields(annis_server)

	logger.info("Rebuilding %d SearchFields, and SearchFieldValues" % len(search_fields))
	SearchField.objects.all().delete()

	splittable_names = [sm.name for sm in SpecialMeta.objects.filter(splittable=True)]

	saved_SearchFieldValues = {}  # (search_field ID, title) -> SearchFieldValue

	# Add all new search fields and mappings
	for search_field in search_fields:
		sf = SearchField()
		sf.title = search_field['name']

		# Save the search field so that it has an id to be added to the
		# search field value search_field foreign key attribute
		sf.save()

		# Save value data
		for value in search_field['values']:
			value_value = value['value']
			split_values = value_value.split(',') if search_field['name'] in splittable_names else [value_value]

			for split_value in split_values:
				title = split_value.strip()

				sfv = saved_SearchFieldValues.get((sf.id, title))
				if not sfv:
					sfv = SearchFieldValue()
					sfv.search_field = sf
					sfv.title = title
					sfv.save()
					saved_SearchFieldValues[(sf.id, title)] = sfv

				text_ids = value['texts']
				if text_ids:
					# Add the texts via the native add ManyToMany handling
					for sfv_text in Text.objects.filter(id__in=text_ids):
						sfv.texts.add(sfv_text)


def _fields(annis_server):
	from texts.models import Text

	search_fields = []  # List of dict of 'name', 'values', where 'values' is a list of dict of 'value', 'texts'

	all_texts = Text.objects.all()
	logger.info("Fetching metadata annotations for %d texts" % len(all_texts))

	corpus_names_by_id = {c.id: c.annis_corpus_name for c in Corpus.objects.all()}

	for text in all_texts:
		corpus_name = corpus_names_by_id.get(text.corpus_id)
		if not text.corpus_id:
			logger.warn('No corpus ID for text %d %s' % (text.id, text.title))
		else:
			meta_query_url = annis_server.url_document_metadata(corpus_name, text.title)
			logger.info(text.title)

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
