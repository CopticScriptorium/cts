import json
from api.json import json_view
from api.encoder import coptic_encoder
from texts.models import Text, Corpus, SearchFieldValue, HtmlVisualization, HtmlVisualizationFormat, TextMeta
from ingest.tasks import shared_task_spawn_single_ingest
import functools

ALLOWED_MODELS = ['texts', 'corpus']
CLASSES = (Text, Corpus)


@json_view()
def api(request, params):
    'Search with the search params from the client-side application'
    get = request.GET
    params = params.split("/")
    params = _process_param_values(params, get)

    return _query(params)


def _query(params={}):
    'Search and return data via the JSON API'

    objects = {}

    if 'model' in params:
        model = params['model']

        if model == 'corpus':
            if 'filters' in params:

                corpus_ids, text_ids, selected_texts = _find_ids_by_field(params['filters'])
                corpora = Corpus.objects.filter(id__in=set(corpus_ids))

                if selected_texts:
                    for corpus in corpora:
                        corpus.texts = [text for text in selected_texts if text.corpus.id == corpus.id]
                elif text_ids:
                    for corpus in corpora:
                        corpus.texts = Text.objects.filter(id__in=text_ids,
                                                           corpus=corpus.id).prefetch_related().order_by('slug')
                else:  # Get all the texts for each corpus
                    for corpus in corpora:
                        corpus.texts = Text.objects.filter(corpus=corpus.id).prefetch_related().order_by('slug')


            else:  # There are no filters. Check for specific corpus.
                if 'corpus' in params and 'slug' in params['corpus']:
                    corpora = Corpus.objects.filter(slug=params['corpus']['slug'])
                else:
                    corpora = Corpus.objects.all()

                for corpus in corpora:
                    corpus.texts = Text.objects.filter(corpus=corpus.id).prefetch_related().order_by('slug')

            # fetch the results and add to the objects dict
            _json_prepare_queryset(objects, 'corpus', corpora)

        # Otherwise, if this is a query to the texts model
        elif model == 'texts':
            if 'corpus' in params and 'slug' in params['corpus'] and \
               'text'   in params and 'slug' in params['text']:
                corpus = Corpus.objects.get(slug=params['corpus']['slug'])
                texts = Text.objects.filter(slug=params['text']['slug'], corpus=corpus.id).prefetch_related()
            else:
                objects['error'] = 'No Text Query specified--missing corpus slug or text slug'
                return objects

            # fetch the results and add to the objects dict
            _json_prepare_queryset(objects, 'texts', texts)

    # If the manifest is set in the params, render site manifest
    elif 'manifest' in params:
        # set up the manifest of the archive
        # Add more in the future

        corpora = Corpus.objects.all()

        for corpus in corpora:
            corpus.texts = Text.objects.filter(corpus=corpus.id).prefetch_related().order_by('slug')

        # fetch the results and add to the objects dict
        _json_prepare_queryset(objects, 'corpus', corpora)

    # If urns is set in the params, return index of urns
    elif 'urns' in params:

        corpora = Corpus.objects.all()
        objects['urns'] = []

        # Get the urns for all corpora
        for corpus in corpora:
            # Add a nested list for the urns related to this corpus
            urn_list = []
            objects['urns'].append(urn_list)

            # Add the initial corpus_urn
            urn_list.append('urn:cts:copticLit:' + corpus.urn_code)

            # Get the texts for the corpus to find their URNs
            corpus.texts = Text.objects.filter(corpus=corpus.id).prefetch_related().order_by('slug')

            # Then add all the urns for texts related to the corpus
            for text in corpus.texts:

                # Fetch the text meta to look for an msName
                # If the meta_item is msName, add it to the text urn
                for meta_item in text.text_meta.all():

                    if meta_item.name == 'document_cts_urn':
                        text_urn = meta_item.value

                # Add the text URN with the doc name from ANNIS to the collection urns
                urn_list.append(text_urn)

                # Add the URNs for the HTML visualizations
                for visualization in text.html_visualizations.all():
                    urn_list.append(text_urn + '/' + visualization.visualization_format.slug + '/html')

                # Add TEI, Paula, reIANNIS, and ANNIS UI
                for suffix in ('/tei/xml', '/paula/xml', '/relannis', '/annis'):
                    urn_list.append(text_urn + suffix)

    # If ingest is in the params, re-ingest the specified text id
    elif 'ingest' in params:
        shared_task_spawn_single_ingest.delay(params['text_id'])
        objects['ingest_res'] = params['text_id']

    # Otherwise, no query is specified
    else:
        objects['error'] = 'No Query specified'

    return objects


def _find_ids_by_field(filters):
    corpus_ids_by_field = {}
    text_ids_by_field = {}
    selected_texts = []

    for filter in filters:
        field_name = filter['field']
        corpus_ids = corpus_ids_by_field.get(field_name, [])
        text_ids   = text_ids_by_field  .get(field_name, [])

        if field_name == 'corpus_urn':
            selected_texts += get_corpus_texts(filter['filter'], corpus_ids)
        elif field_name == 'textgroup_urn':
            selected_texts += get_textgroup_texts(filter['filter'], corpus_ids)
        else:
            sfv = SearchFieldValue.objects.filter(id=filter['id'])
            text_ids += list(sfv.values_list('texts__id', flat=True))
            corpus_ids += [text.corpus.id for text in Text.objects.filter(id__in=text_ids)]

        if corpus_ids:
            corpus_ids_by_field[field_name] = corpus_ids
        if text_ids:
            text_ids_by_field[field_name] = text_ids

    return _intersect(corpus_ids_by_field), _intersect(text_ids_by_field), selected_texts


def _intersect(ids_dict):
    ids_sets = [set(values) for values in ids_dict.values()]
    return functools.reduce(lambda a, b: a & b, ids_sets)


def _json_prepare_queryset(objects, model_name, queryset):
    if not model_name in objects:
        objects[model_name] = []
    model_objects = objects[model_name]

    for item in queryset:

        # Check if the item is an instance of our defined classes
        if isinstance(item, CLASSES):
            # if it is an instance of a class, append the dict
            item = coptic_encoder(item)

        # Finally, add the item to the objects response at the model
        model_objects.append(item)

    return objects


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

        elif 'manifest' in query_dict:
            clean['manifest'] = True

        elif 'urns' in query_dict:
            clean['urns'] = True

        elif 'ingest' in query_dict:
            clean['ingest'] = True
            clean['text_id'] = query_dict['id'].strip()

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


def get_corpus_texts(filter_value, corpus_ids):
    'Look up texts based on corpus URN data from the document_cts_urn'
    selected_texts = []
    matched_text_meta_objects = []
    filter_value = filter_value.split('.')

    # Compare document_cts_urn meta values to the filter_value from the search params
    for text_meta_object in TextMeta.objects.filter(name='document_cts_urn'):
        parsed_urn = text_meta_object.value.split(':')
        parsed_urn = parsed_urn[3].split('.')
        if parsed_urn[0] == filter_value[0] and parsed_urn[1] == filter_value[1]:
            matched_text_meta_objects.append(text_meta_object)

    # Get the textMeta msName items
    for matched_text_meta_object in matched_text_meta_objects:
        selected_texts += list(Text.objects.filter(text_meta=matched_text_meta_object.id))

    # Aggregate the corpus ids for each text
    for sel_text in selected_texts:
        if sel_text.corpus.id not in corpus_ids:
            corpus_ids.append(sel_text.corpus.id)

    return selected_texts


def get_textgroup_texts(filter_value, corpus_ids):
    'Look up texts based on textgroup URN data from the document_cts_urn'
    selected_texts = []
    matched_text_meta_objects = []

    # Compare document_cts_urn meta values to the filter_value from the search params
    for text_meta_object in TextMeta.objects.filter(name='document_cts_urn'):
        parsed_urn = text_meta_object.value.split(':')
        parsed_urn = parsed_urn[3].split('.')
        if parsed_urn[0] == filter_value:
            matched_text_meta_objects.append(text_meta_object)

    # Get the textMeta msName items
    for matched_text_meta_object in matched_text_meta_objects:
        selected_texts += list(Text.objects.filter(text_meta=matched_text_meta_object.id))

    # Aggregate the corpus ids for each text
    for sel_text in selected_texts:
        if sel_text.corpus.id not in corpus_ids:
            corpus_ids.append(sel_text.corpus.id)

    return selected_texts
