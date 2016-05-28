import logging
from django.shortcuts import redirect
import json
from api.json import json_view
from api.encoder import encode
from texts.models import Text, Corpus, SearchFieldValue, TextMeta
import functools

log = logging.getLogger(__name__)
TEXT_PREFETCH_FIELDS = 'html_visualizations'
ALLOWED_MODELS = ('texts', 'corpus', 'urn')


@json_view()
def api(request, params):
    'Search with the search params from the client-side application'
    get = request.GET
    log.info('API called with %s, %s' % (request, params))

    return _query(_process_param_values(params.split("/"), get))


def search(request):
	def params_with_searchfieldvalue_ids(values_by_key):
		for key, values_list in values_by_key.lists():  # Example: corpus: [c1, c2]
			for value in values_list:
				for sfv in SearchFieldValue.objects.filter(search_field__title=key, title=value):
					yield key, sfv.id, value

	params = [('%s=%d:%s' % param) for param in params_with_searchfieldvalue_ids(request.GET)]
	return redirect('/filter/' + '&'.join(params) if params else '/')

def _query(params):
    'Search and return data via the JSON API'

    objects = {}

    if 'model' in params:
        model = params['model']

        if model == 'urn' and 'urn' in params:
            _process_urn_request(params['urn'], objects)
        elif model == 'corpus':
            if 'filters' in params:
                corpus_ids, text_ids = _corpus_and_text_ids_from_filters(params['filters'])
                corpora = Corpus.objects.filter(id__in=set(corpus_ids))

                if text_ids:
                    _add_texts_to_corpora(corpora, text_ids)
                else:
                    _add_texts_to_corpora(corpora)

            else:  # There are no filters. Check for specific corpus.
                if 'corpus' in params and 'slug' in params['corpus']:
                    corpora = Corpus.objects.filter(slug=params['corpus']['slug'])
                else:
                    corpora = Corpus.objects.all()

                _add_texts_to_corpora(corpora)

            # fetch the results and add to the objects dict
            objects['corpus'] = _json_from_queryset(corpora)

        # Otherwise, if this is a query to the texts model
        elif model == 'texts':
            if 'corpus' in params and 'slug' in params['corpus'] and \
               'text'   in params and 'slug' in params['text']:
                corpus = Corpus.objects.get(slug=params['corpus']['slug'])
                text = Text.objects.filter(slug=params['text']['slug'], corpus=corpus.id).prefetch_related(TEXT_PREFETCH_FIELDS).first()
            else:
                objects['error'] = 'No Text Query specified--missing corpus slug or text slug'
                return objects

            # fetch the results and add to the objects dict
            objects['text'] = encode(text)

    # Otherwise, no query is specified
    else:
        objects['error'] = 'No Query specified'

    return objects


def _process_urn_request(urn, objects):
    texts = texts_for_urn(urn)

    # Find the corpora containing the matching texts
    corpus_ids = set([text.corpus_id for text in texts])
    corpora = Corpus.objects.filter(id__in=corpus_ids)

    _add_texts_to_corpora(corpora, texts=texts)
    objects['corpus'] = _json_from_queryset(corpora)


def texts_for_urn(urn):
    # Find texts matching the URN using their metadata
    matching_tm_ids = TextMeta.objects.filter(name='document_cts_urn', value__iregex='^' + urn + r'($|[\.:])'
    	).values_list('id', flat=True)
    texts = Text.objects.filter(text_meta__name='document_cts_urn',
        text_meta__id__in=matching_tm_ids).order_by('slug')
    return texts


def _add_texts_to_corpora(corpora, text_ids=None, texts=None):
    adding_texts = texts if texts else \
		(Text.objects.filter(id__in=text_ids) if text_ids else Text.objects.all()).\
        select_related('corpus').order_by('slug')
    for corpus in corpora:
        corpus.texts = [t for t in adding_texts if t.corpus_id == corpus.id]


def _corpus_and_text_ids_from_filters(filters):
    corpus_ids_by_field = {}
    text_ids_by_field = {}

    for filter in filters:
        field_name = filter['field']
        corpus_ids = corpus_ids_by_field.get(field_name, set())
        text_ids   = text_ids_by_field  .get(field_name, set())

        sfv = SearchFieldValue.objects.filter(id=filter['id'])
        text_ids.update(sfv.values_list('texts__id', flat=True))
        corpus_ids.update((text.corpus_id for text in Text.objects.filter(id__in=text_ids)))

        if corpus_ids:
            corpus_ids_by_field[field_name] = corpus_ids
        if text_ids:
            text_ids_by_field[field_name] = text_ids

    return _intersect_ids_across_fields(corpus_ids_by_field), _intersect_ids_across_fields(text_ids_by_field)


def _intersect_ids_across_fields(id_sets_by_fieldname):
	ids_sets = [id_set for id_set in id_sets_by_fieldname.values()]

	def intersect_sets(set1, set2):
		'Intersect IDs in successive sets to ensure the remaining IDs are in all sets'
		intersection = set1 & set2
		log.debug('Intersection of %s and %s is %s' % (set1, set2, intersection))
		return intersection

	return functools.reduce(intersect_sets, ids_sets) if ids_sets else []


def _json_from_queryset(queryset):
    return [encode(item) for item in queryset]


def _process_param_values(params, query_dict):
    'Process the param values to improve security'
    clean = {}

    if query_dict:
        # first, process the type of query by model or manifest
        if 'model' in query_dict:
            if query_dict['model'] in ALLOWED_MODELS:
                clean['model'] = query_dict['model']

            if 'corpus_slug' in query_dict:
                clean['corpus'] = {
                    'slug': query_dict['corpus_slug'].strip()
                }

            if 'text_slug' in query_dict:
                clean['text'] = {
                    'slug': query_dict['text_slug'].strip()
                }

            if 'urn_value' in query_dict:
                clean['urn'] = query_dict['urn_value'].strip()

        # Then process the supplied query
        filters = [json.loads(filter) for filter in query_dict.getlist('filters')]
        if filters:
            clean['filters'] = filters

    else:
        if 'manifest' in params:
            clean['manifest'] = True

        elif 'urns' in params:
            clean['urns'] = True

    return clean
