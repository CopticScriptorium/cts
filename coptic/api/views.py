import pdb
import json
from api.json import json_view
from texts.models import Text, Corpus, SearchFieldValue, HtmlVisualization, HtmlVisualizationFormat, TextMeta

ALLOWED_MODELS = ['texts', 'corpus']
CLASSES = ( Text, Corpus )

@json_view()
def api(request, _params=None):
	"""
	Search with the search params from the via the client-side application
	"""
	params = {}
	get = request.GET

	if _params != None:
		params = process_param_values( _params, get )
		pass

	return _query( params ) 

# Basic search implementation for returning data via the JSON API
def _query( params={} ):
	"""
	Query the database with the sanitized params
	"""

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

					# Do a textsearch across the corpora
					elif f['field'] == "text_search":
						ts_corpus = Corpus.objects.all()

						for ts_corpus in ts_corpus:
							corpus_has_textsearch_match = False
							ts_texts = Text.objects.filter(corpus=ts_corpus.id)

							for ts_text in ts_texts:
								ts_html_visualizations = ts_text.html_visualizations.all()

								for ts_html_visualization in ts_html_visualizations:
									if f['filter'] in ts_html_visualization.html:
										corpus_has_textsearch_match = True
										break

								if corpus_has_textsearch_match == True:
									break

							if corpus_has_textsearch_match:
								corpus_ids.append( ts_corpus.id )

					# Otherwise, treat it as a general meta query to the ANNIS metadata ingested
					# as searchfields
					else:
						sfv = SearchFieldValue.objects.filter(id=f['id'])
						text_ids = text_ids + list( sfv.values_list('texts__id', flat=True) )
						search_texts = Text.objects.filter( id__in=text_ids )
						for text in search_texts:
							corpus_ids.append(text.corpus.id)


				# If we have selected texts to filter and join
				if len( selected_texts ):

					# Get Unique values from the ids
					cid_set = set(corpus_ids)
					corpus_ids = set(cid_set)

					# query corpus and texts
					corpus = Corpus.objects.filter(id__in=corpus_ids)
					for corpus in corpus:

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
					corpus = Corpus.objects.filter(id__in=corpus_ids)
					for corpus in corpus:
						corpus.texts = Text.objects.filter(id__in=text_ids, corpus=corpus.id ).prefetch_related().order_by('slug')


				# Otherwise, get all the texts for each corpus/corpus 
				else:

					# Get Unique values from the ids
					cid_set = set(corpus_ids)
					corpus_ids = set(cid_set)

					# query corpus and texts
					corpus = Corpus.objects.filter(id__in=corpus_ids)
					for corpus in corpus:

						corpus.texts = Text.objects.filter(corpus=corpus.id ).prefetch_related().order_by('slug')

			# There are no filters, check for specific corpus
			else:

				# If there's a slug to query a specific corpus
				if "query" in params and "slug" in params['query']:
					corpus = Corpus.objects.filter(slug=params['query']['slug'])
				else:
					# establish all the queries to be run
					corpus = Corpus.objects.all()

				# Query texts for the corpus
				for corpus in corpus:
					# Ensure prefetch related
					corpus.texts = Text.objects.filter(corpus=corpus.id ).prefetch_related().order_by('slug')


			# fetch the results and add to the objects dict
			jsonproof_queryset(objects, 'corpus', corpus)


		# Otherwise, if this is a query to the texts model
		elif params['model'] == 'texts':

			if "query" in params and "slug" in params['query']:
				texts = Text.objects.filter( slug=params['query']['slug'] ).prefetch_related()

				# for text in texts:
				#	text.meta = SearchFieldValue.objects.filter(corpus__id=text.corpus.id)

			else:
				texts = Text.objects.filter()

			# fetch the results and add to the objects dict
			jsonproof_queryset(objects, 'texts', texts)
				

	# If the manifest is set in the params, render site manifest 
	elif 'manifest' in params:
		# setup the manifest of the archive
		# Add more in the future

		corpus = Corpus.objects.all()

		for corpus in corpus:
			corpus.texts = Text.objects.filter(corpus=corpus.id).prefetch_related().order_by('slug')

		# fetch the results and add to the objects dict
		jsonproof_queryset(objects, 'corpus', corpus)


	# If urns is set in the params, return index of urns
	elif 'urns' in params:

		corpus = Corpus.objects.all()

		objects['urns'] = []

		# Get the urns for all corpus
		for i, corpus in enumerate( corpus ):

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
def process_param_values( params, get ):
	clean = {}
	params = params.split("/")

	if len( params ) > 0:

		# first, process the type of query by model or manifest
		if params[0] in ALLOWED_MODELS:
			clean['model'] = params[0]

		elif params[0] == "manifest":
			clean['manifest'] = True

		elif params[0] == "urns":
			clean['urns'] = True

		# Then process the supplied query
		# Query should be included in api like this: 
		# /api/[model]/slug:foobar,id:1,etc.etc.
		# Add more sanitization in future steps
		if len( params ) > 1:
			query = params[1].split(",")
			clean['query'] = {}
			for item in query:
				item = item.split(":")

				if len( item ) > 1:
					clean['query'][ item[0] ] = item[1]

	_filters = get.getlist("filters") 
	filters = []
	if len( _filters ):
		for f in _filters:
			filters.append( json.loads(f) )
		clean['filters'] = filters

	return clean


# Define custom encoder for the queryset model class instances
def coptic_encoder( obj ):

	encoded = {}

	# If we're dumping an instance of the Text class to JSON
	if isinstance(obj, Text):
		text = {}

		text['title'] = obj.title 
		text['slug'] = obj.slug 
		text['html_visualizations'] = []
		text['text_meta'] = []

		for text_meta in obj.text_meta.all(): 
			if text_meta.name == "msName":
				text['msName'] = text_meta.value.replace(".", "-")

			text['text_meta'].append({
					'name' : text_meta.name,
					'value' : text_meta.value 
				})

		for html_visualization in obj.html_visualizations.all():
			text['html_visualizations'].append({
					"title" : html_visualization.visualization_format.title,
					"slug" : html_visualization.visualization_format.slug,
					"html" : html_visualization.html
				})

		text['corpus'] = coptic_encoder( obj.corpus )

		encoded = text

	# If we're dumping an instance of the Corpus class to JSON
	elif isinstance(obj, Corpus):
		corpus = {}

		corpus['title'] = obj.title 
		corpus['urn_code'] = obj.urn_code 
		corpus['textgroup_urn_code'] = obj.textgroup_urn_code 
		corpus['html_corpora_code'] = obj.html_corpora_code 
		corpus['slug'] = obj.slug 
		corpus['annis_code'] = obj.annis_code 
		corpus['annis_corpus_name'] = obj.annis_corpus_name
		corpus['github'] = obj.github 
		corpus['html_visualization_formats'] = []

		for html_visualization_format in obj.html_visualization_formats.all():
			corpus['html_visualization_formats'].append({
					'title' : html_visualization_format.title,
					'slug' : html_visualization_format.slug
				}) 

		if hasattr(obj, 'texts'):
			corpus['texts'] = []
			for i, text in enumerate( obj.texts ):
				corpus['texts'].append({
						'id' : text.id,
						'title' : text.title,
						'slug' : text.slug,
						'html_visualizations' : [] 
					})
				for html_visualization in text.html_visualizations.all():
					corpus['texts'][ i ]['html_visualizations'].append({
							"title" : html_visualization.visualization_format.title,
							"slug" : html_visualization.visualization_format.slug
						})

		encoded = corpus

	return encoded 


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
