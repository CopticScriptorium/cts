import pdb
import json
from api.json import json_view
from texts.models import Text, Collection, Author, SearchFieldValue, HtmlVisualization, HtmlVisualizationFormat, TextMeta
from ingest.models import Ingest

ALLOWED_MODELS = ['texts', 'collections']
CLASSES = ( Text, Collection )

@json_view
def api(request, __params__=None):
	"""
	Search with the search params from the via the client-side application
	"""
	params = {}
	get = request.GET

	if __params__ != None:
		params = process_param_values( __params__, get )
		pass

	return _query( params ) 

# basic search implementation for returning data 
def _query( params={} ):
	"""
	Query the database with the sanitized params
	"""

	search_filter = {}
	objects = {} 

	# If there's a model to query, such as collections or texts
	if 'model' in params:
		most_recent_ingests = Ingest.objects.all().order_by('-id')
		if len( most_recent_ingests ) > 0:
			most_recent_ingest = most_recent_ingests[0]
			mss_texts = []

			# If this is a query to the collections model
			if params['model'] == 'collections':

				# If there are search filters included with the sanitized params
				if "filters" in params:

					collection_ids = []
					text_ids = []

					# Process the filters and find the collections based on the ID
					for f in params['filters']:
						if f['field'] == "corpus_urn":	
							corpus_collections = Collection.objects.filter(urn_code=f['filter'])
							for c in corpus_collections:
								collection_ids.append( c.id )

						elif f['field'] == "mss_urn":	

							cid_set = []
							collection_ids = []

							text_meta_items = TextMeta.objects.filter(name="msName", value=f['filter'])

							# Get the textMeta msName items
							for text_meta_item in text_meta_items:
								mss_texts = mss_texts + list( Text.objects.filter(text_meta=text_meta_item.id) )

							for mss_text in mss_texts:
								collection_ids.append(mss_text.collection.id)

						elif f['field'] == "text_search":
							ts_collections = Collection.objects.all()

							for ts_collection in ts_collections:
								collection_has_textsearch_match = False
								ts_texts = Text.objects.filter(collection=ts_collection.id)

								for ts_text in ts_texts:
									ts_html_visualizations = ts_text.html_visualizations.all()

									for ts_html_visualization in ts_html_visualizations:
										if f['filter'] in ts_html_visualization.html:
											collection_has_textsearch_match = True
											break

									if collection_has_textsearch_match == True:
										break

								if collection_has_textsearch_match:
									collection_ids.append( ts_collection.id )

						else:
							sfv = SearchFieldValue.objects.filter(id=f['id'])
							text_ids = text_ids + list( sfv.values_list('texts__id', flat=True) )
							search_texts = Text.objects.filter( id__in=text_ids )
							for text in search_texts:
								collection_ids.append(text.collection.id)

					# If we have MSS texts to filter and join
					if len( mss_texts ):

						# query collections and texts
						collections = Collection.objects.filter(id__in=collection_ids)
						for collection in collections:
							if not hasattr( collection, "texts"):
								collection.texts = []

							for text in mss_texts:
								if text.collection.id == collection.id:
									collection.texts.append( text )

					# If we have other texts to filter and join
					if len( text_ids ):

						# Get Unique values from the ids
						cid_set = set(collection_ids)
						collection_ids = set(cid_set)

						# query collections and texts
						collections = Collection.objects.filter(id__in=collection_ids)
						for collection in collections:
							collection.texts = Text.objects.filter(id__in=text_ids, collection=collection.id, ingest=most_recent_ingest.id, ).prefetch_related().order_by('slug')



					# Otherwise, get all the texts for each collection/corpus 
					else:

						# Get Unique values from the ids
						cid_set = set(collection_ids)
						collection_ids = set(cid_set)

						# query collections and texts
						collections = Collection.objects.filter(id__in=collection_ids)
						for collection in collections:

							collection.texts = Text.objects.filter(collection=collection.id, ingest=most_recent_ingest.id, ).prefetch_related().order_by('slug')

				else:

					# If there's a slug to query a specific collection
					if "query" in params and "slug" in params['query']:
						collections = Collection.objects.filter(slug=params['query']['slug'])
					else:
						# establish all the queries to be run
						collections = Collection.objects.all()

					for collection in collections:
						collection.texts = Text.objects.filter(collection=collection.id, ingest=most_recent_ingest.id).prefetch_related().order_by('slug')

				# fetch the results and add to the objects dict
				jsonproof_queryset(objects, 'collections', collections)


			# Otherwise, if this is a query to the texts model
			elif params['model'] == 'texts':

				if "query" in params and "slug" in params['query']:
					texts = Text.objects.filter(slug=params['query']['slug'], ingest=most_recent_ingest.id).prefetch_related()

					# for text in texts:
					#	text.meta = SearchFieldValue.objects.filter(collections__id=text.collection.id)

				else:
					texts = Text.objects.filter(ingest=most_recent_ingest.id)

				# fetch the results and add to the objects dict
				jsonproof_queryset(objects, 'texts', texts)
				

	# If the manifest is set in the params, render site manifest 
	elif 'manifest' in params:
		# setup the manifest of the archive
		# Add more in the future

		# establish all the queries to be run if there is ingest data
		most_recent_ingests = Ingest.objects.all().order_by('-id')
		if len( most_recent_ingests ) > 0:

			most_recent_ingest = most_recent_ingests[0]
			collections = Collection.objects.all()

			for collection in collections:
				collection.texts = Text.objects.filter(collection=collection.id, ingest=most_recent_ingest.id).prefetch_related().order_by('slug')

			# fetch the results and add to the objects dict
			jsonproof_queryset(objects, 'collections', collections)

		# In case there is no ingest data, just return the collections
		else:
			collections = Collection.objects.all()

	# If urns is set in the params, return index of urns
	elif 'urns' in params:

		# establish all the queries to be run if there is ingest data
		most_recent_ingests = Ingest.objects.all().order_by('-id')
		most_recent_ingest = most_recent_ingests[0]
		collections = Collection.objects.all()

		objects['urns'] = []

		# Get the urns for all collections
		for i, collection in enumerate( collections ):

			# Add a nested list for the urns related to this collection
			objects['urns'].append([])

			# Set the initial collection_urn	
			collection_urn = "urn:cts:copticLit:" + collection.urn_code

			# Add the collection urn to the collection urn list
			objects['urns'][i].append( collection_urn )

			# Get the texts for the collection to find their URNs
			collection.texts = Text.objects.filter(collection=collection.id, ingest=most_recent_ingest.id).prefetch_related().order_by('slug')

			# Then add all the urns for texts related to the collection
			for text in collection.texts:

				# The base of the text_urn will be the collection urn
				text_urn = collection_urn + ":"

				# Fetch the text meta to look for an msName
				text_meta = text.text_meta.all()

				# If the meta_item is msName, add it to the text urn
				for meta_item in text_meta:

					if meta_item.name == "msName":
						text_urn = text_urn + meta_item.value 

						# If we have a msName, add that msName URN to the collection urns
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
				objects['urns'][i].append( text_urn + "/reiannis" )
				objects['urns'][i].append( text_urn + "/annis" )


	# Otherwise, no query is specified
	else:
		objects['error'] = "No Query specified";

	return objects 

# Dump an object to JSON
def to_JSON(obj):
	return json.dumps(obj, default=lambda o: o.__dict__, sort_keys=True, indent=4)

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
			item = json.dumps( item, cls=CopticEncoder )


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
class CopticEncoder(json.JSONEncoder):

	def default(self, obj):

		# If we're dumping an instance of the Text class to JSON
		if isinstance(obj, Text):
			text = {}

			text['title'] = obj.title 
			text['slug'] = obj.slug 
			text['collection'] = obj.collection
			text['html_visualizations'] = []
			text['text_meta'] = []

			for text_meta in obj.text_meta.all(): 
				if text_meta.name == "msName":
					text['msName'] = text_meta.value

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

			return text

		# If we're dumping an instance of the Collection class to JSON
		elif isinstance(obj, Collection):
			collection = {}

			collection['title'] = obj.title 
			collection['urn_code'] = obj.urn_code 
			collection['html_corpora_code'] = obj.html_corpora_code 
			collection['slug'] = obj.slug 
			collection['annis_code'] = obj.annis_code 
			collection['annis_corpus_name'] = obj.annis_corpus_name
			collection['github'] = obj.github 
			collection['html_visualization_formats'] = []

			for html_visualization_format in obj.html_visualization_formats.all():
				collection['html_visualization_formats'].append({
						'title' : html_visualization_format.title,
						'slug' : html_visualization_format.slug
					}) 

			if hasattr(obj, 'texts'):
				collection['texts'] = []
				for i, text in enumerate( obj.texts ):
					collection['texts'].append({
							'id' : text.id,
							'title' : text.title,
							'slug' : text.slug,
							'html_visualizations' : [] 
						})
					for html_visualization in text.html_visualizations.all():
						collection['texts'][ i ]['html_visualizations'].append({
								"title" : html_visualization.visualization_format.title,
								"slug" : html_visualization.visualization_format.slug,
								"html" : html_visualization.html
							})

			return collection 

		# Let the base class default method raise the TypeError
		return json.JSONEncoder.default(self, obj)


