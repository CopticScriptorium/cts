import pdb
import json
from api.json import json_view
from api.encoder import coptic_encoder
from texts.models import Text, Corpus, SearchFieldValue, HtmlVisualization, HtmlVisualizationFormat, TextMeta

ALLOWED_MODELS = ['texts', 'corpus']
CLASSES = ( Text, Corpus )

@json_view()
def api( request ):
	"""
	Search with the search params from the via the client-side application
	"""
	get = request.GET
	params = process_param_values( get )

	return _query( params ) 

# Basic search implementation for returning data via the JSON API
def _query( params={} ):
	"""
	Query the database with the sanitized params
	"""
	print(params)

	search_filter = {}
	objects = {} 

	# If there's a model to query, such as corpus or texts
	if 'model' in params:
		selected_texts = []

		# If this is a query to the corpus model
		if params['model'] == 'corpus':

			# If there are search filters included with the sanitized params
			if "filters" in params:

				corpus_ids = []
				text_ids = []

				# Process the filters and find the corpus based on the ID
				for f in params['filters']:

					# Lookup by corpus URN data from ANNIS
					if f['field'] == "corpus_urn":	
						corpus_ids, selected_texts = get_corpus_texts( f['filter'], corpus_ids, selected_texts )

					# Lookup by textgroup URN data from ANNIS
					elif f['field'] == "textgroup_urn":	
						corpus_ids, selected_texts = get_textgroup_texts( f['filter'], corpus_ids, selected_texts )

					# Otherwise, treat it as a general meta query to the ANNIS metadata ingested
					# as searchfields
					else:
						sfv = SearchFieldValue.objects.filter( id=f['id'] )
						text_ids = text_ids + list( sfv.values_list('texts__id', flat=True) )
						search_texts = Text.objects.filter( id__in=text_ids )
						for text in search_texts:
							corpus_ids.append( text.corpus.id )


				# If we have selected texts to filter and join
				if len( selected_texts ):

					# Get Unique values from the ids
					cid_set = set(corpus_ids)
					corpus_ids = set(cid_set)

					# Query corpus and texts
					corpora = Corpus.objects.filter(id__in=corpus_ids)
					for corpus in corpora:
						corpus.texts = []
						for text in selected_texts:
							if text.corpus.id == corpus.id:
								corpus.texts.append( text )

				# If we have other texts to filter and join
				elif len( text_ids ):

					# Get Unique values from the ids
					cid_set = set(corpus_ids)
					corpus_ids = set(cid_set)

					# query corpus and texts
					corpora = Corpus.objects.filter(id__in=corpus_ids)
					for corpus in corpora:
						corpus.texts = Text.objects.filter(id__in=text_ids, corpus=corpus.id ).prefetch_related().order_by('slug')


				# Otherwise, get all the texts for each corpus/corpus 
				else:

					# Get Unique values from the ids
					cid_set = set(corpus_ids)
					corpus_ids = set(cid_set)

					# query corpus and texts
					corpora = Corpus.objects.filter(id__in=corpus_ids)
					for corpus in corpora:

						corpus.texts = Text.objects.filter(corpus=corpus.id ).prefetch_related().order_by('slug')

			# There are no filters, check for specific corpus
			else:

				# If there's a slug to query a specific corpus
				if "query" in params and "slug" in params['query']:
					corpora = Corpus.objects.filter( slug=params['query']['slug'] )
				else:
					# establish all the queries to be run
					corpora = Corpus.objects.all()

				# Query texts for the corpus
				for corpus in corpora:
					# Ensure prefetch related
					corpus.texts = Text.objects.filter( corpus=corpus.id ).prefetch_related().order_by('slug')


			# fetch the results and add to the objects dict
			jsonproof_queryset(objects, 'corpus', corpora)


		# Otherwise, if this is a query to the texts model
		elif params['model'] == 'texts':

			if "query" in params and "slug" in params['query']:
				texts = Text.objects.filter( slug=params['query']['slug'] ).prefetch_related()

				# for text in texts:
				#	text.meta = SearchFieldValue.objects.filter(corpus__id=text.corpus.id)

			else:
				texts = Text.objects.filter()

			# fetch the results and add to the objects dict
			jsonproof_queryset( objects, 'texts', texts )
				

	# If the manifest is set in the params, render site manifest 
	elif 'manifest' in params:
		# setup the manifest of the archive
		# Add more in the future

		corpora = Corpus.objects.all()

		for corpus in corpora:
			corpus.texts = Text.objects.filter( corpus=corpus.id ).prefetch_related().order_by( 'slug' )

		# fetch the results and add to the objects dict
		jsonproof_queryset( objects, 'corpus', corpora )


	# If urns is set in the params, return index of urns
	elif 'urns' in params:

		corpora = Corpus.objects.all()

		objects['urns'] = []

		# Get the urns for all corpus
		for i, corpus in enumerate( corpora ):

			# Add a nested list for the urns related to this corpus
			objects['urns'].append([])

			# Set the initial corpus_urn	
			corpus_urn = "urn:cts:copticLit:" + corpus.urn_code

			# Add the corpus urn to the corpus urn list
			objects['urns'][i].append( corpus_urn )

			# Get the texts for the corpus to find their URNs
			corpus.texts = Text.objects.filter(corpus=corpus.id).prefetch_related().order_by('slug')

			# Then add all the urns for texts related to the corpus
			for text in corpus.texts:

				# The base of the text_urn will be the corpus urn
				text_urn = corpus_urn + ":"

				# Fetch the text meta to look for an msName
				text_meta = text.text_meta.all()

				# If the meta_item is msName, add it to the text urn
				for meta_item in text_meta:

					if meta_item.name == "msName":
						text_urn = text_urn + meta_item.value 

						# If we have a msName, add that msName URN to the corpus urns
						if text_urn not in objects['urns'][i]:
							objects['urns'][i].append( text_urn )

						# Then add a final colon for the document urns
						text_urn = text_urn + ":"

				# Then add the text doc name from ANNIS
				text_urn = text_urn + text.slug

				# Add the text URN with the doc name from ANNIS to the collecition urns
				objects['urns'][i].append( text_urn )

				# Add the URNs for the HTML visualizations
				html_visualizations = text.html_visualizations.all()
				for visualization in html_visualizations:
					objects['urns'][i].append( text_urn + "/" + visualization.visualization_format.title + "/html" )

				# Add TEI, Paula, reIANNIS, and ANNIS UI
				objects['urns'][i].append( text_urn + "/tei/xml" )
				objects['urns'][i].append( text_urn + "/paula/xml" )
				objects['urns'][i].append( text_urn + "/relannis" )
				objects['urns'][i].append( text_urn + "/annis" )


	# Otherwise, no query is specified
	else:
		objects['error'] = "No Query specified";

	return objects 


# ready a django queryset for json serialization
def jsonproof_queryset(objects, model_name, queryset):

	try: 
		objects[model_name]
	except KeyError:
		objects[model_name] = []

	for item in queryset:

		# Check if the item is an instance of our defined classes 
		if isinstance( item, CLASSES ): 

			# if it is an instance of a class, append the dict
			item = coptic_encoder( item )


		# Finally, add the item to the objects response at the model 
		objects[model_name].append( item )


	return objects


# Process the param values to ensure security
def process_param_values( get ):
	clean = {}

	if get:

			# first, process the type of query by model or manifest
		if "model" in get:	
			if get['model'] in ALLOWED_MODELS:
				clean['model'] = get['model'] 

		elif "manifest" in get:
			clean['manifest'] = True

		elif "urns" in get:
			clean['urns'] = True

		# Then process the supplied query
		_filters = get.getlist("filters") 
		filters = []
		if len( _filters ):
			for f in _filters:
				filters.append( json.loads(f) )
			clean['filters'] = filters

	return clean


def get_corpus_texts( filter_value, corpus_ids, selected_texts ):
	"""
	Lookup texts based on corpus URN data from the document_cts_urn
	"""
	matched_text_meta_objects = []
	filter_value = filter_value.split(".")

	# Compare document_cts_urn meta values to the filter_value from the search params
	for text_meta_object in TextMeta.objects.filter( name="document_cts_urn" ):

		parsed_urn = text_meta_object.value.split(":")
		parsed_urn = parsed_urn[3].split(".")

		if parsed_urn[0] == filter_value[0] and parsed_urn[1] == filter_value[1]:
			matched_text_meta_objects.append( text_meta_object )

	# Get the textMeta msName items
	for matched_text_meta_object in matched_text_meta_objects:
		selected_texts = selected_texts + list( Text.objects.filter( text_meta=matched_text_meta_object.id ) )

	# Aggregate the corpus ids for each text
	for sel_text in selected_texts:
		if sel_text.corpus.id not in corpus_ids:
			corpus_ids.append(sel_text.corpus.id)

	return corpus_ids, selected_texts 


def get_textgroup_texts( filter_value, corpus_ids, selected_texts ):
	"""
	Lookup texts based on textgroup URN data from the document_cts_urn
	"""
	matched_text_meta_objects = []

	# Compare document_cts_urn meta values to the filter_value from the search params
	for text_meta_object in TextMeta.objects.filter( name="document_cts_urn" ):
		parsed_urn = text_meta_object.value.split(":")
		parsed_urn = parsed_urn[3].split(".")
		if parsed_urn[0] == filter_value:
			matched_text_meta_objects.append( text_meta_object )


	# Get the textMeta msName items
	for matched_text_meta_object in matched_text_meta_objects:
		selected_texts = selected_texts + list( Text.objects.filter(text_meta=matched_text_meta_object.id) )

	# Aggregate the corpus ids for each text
	for sel_text in selected_texts:
		if sel_text.corpus.id not in corpus_ids:
			corpus_ids.append(sel_text.corpus.id)


	return corpus_ids, selected_texts 
