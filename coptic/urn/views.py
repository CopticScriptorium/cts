from django.shortcuts import get_object_or_404, redirect, render 
from django.http import HttpResponse
from texts.models import Text, Collection, SearchField, SearchFieldValue 

def urn_redirect(request, query):
	"""
	Redirect the application to the correct text based on an ingested URN
	"""

	query = query.split("/")
	urn = query[0].split(":")
	corpus_urn = urn[3].split(".")
	collection_urn = corpus_urn[0] + "." + corpus_urn[1] 
	author_urn = corpus_urn[0]

	collection = Collection.objects.get( urn_code=collection_urn )
		
	# If it's a xml query, for the moment redirect to github
	if query[-1] == "xml":
		return redirect( collection.github )

	# If it's an REI annis query, redirect to github
	if query[-1] == "relannis":
		return redirect( collection.github )

	# If it's an ANNIS URN, redirect to ANNIS
	if query[-1] == "annis":
		return redirect( "https://corpling.uis.georgetown.edu/annis/scriptorium#_c=" + collection.annis_code )


	# If the urn length is 6, it's definitely a text query
	if len( urn ) == 6: 

		# Check the passage URN against the collection texts metadata
		text_slug = check_passage_urn( urn, collection )

		# A text exists for the URN query parameter 
		if text_slug:
			# Add the slug to the redirect URL  
			url  = "/texts/" + text_slug

			# If it's an HTML query, specify redirect to the html visualization url 
			if query[-1] == "html":
				url = url + "/" + query[-2]

		else:
			# Add the slug to the redirect URL  
			url  = "/"


		return redirect( url ) 

	# If it's a length of 5, this means the URN might be a text or might be a manuscript
	elif len( urn ) == 5: 

		# Check the passage URN against the collection texts metadata
		text_slug = check_passage_urn( urn, collection )

		# A text exists for the URN query parameter 
		if text_slug:

			# Add the text URN slug
			url  = "/texts/" + text_slug 

			# If it's an HTML query, specify redirect to the html visualization url 
			if query[-1] == "html":
				url = url + "/" + query[-2]

		# A text doesn't exist for the URN query parameter, treat it like a manuscript sigla query
		else:

			# It's a collection query, render the collection text index
			url = "/filter/mss_urn=0:" +  urn[4]

		return redirect( url ) 

	# Else if the urn length is 4, it's a corpus/collection query  
	elif len( urn ) == 4:

		# It's a collection query, render the collection text index
		url = "/filter/corpus_urn=" + str( collection.id ) + ":" + collection.urn_code

		return redirect( url )


	# Else, it's an invalid URN
	else: 
		# Invalid URN
		# In the future, add URN not found error notice
		return redirect( "/" )


def check_passage_urn( urn, collection ):

	# Parse the passage URN
	passage_urn = urn[4].split("-") 
	if len( passage_urn ) > 1:
		passage_urn.sort()
		passage_urn_low = passage_urn[0] 
		passage_urn_high = passage_urn[1]

	# Get the texts for the specifed collection to locate the passage
	collection_texts = Text.objects.filter(collection=collection.id)

	# Check the passage urn against each text metadata
	for text in collection_texts:
		gt_pages_from = False
		lt_pages_to = False

		# For each meta item, check if it is pages_from, pages_to, or chapter
		for meta in text.text_meta.all():

			# Check the pages_from / pages_to range against the passage_urn
			if meta.name in ["pages_from", "pages_to"]:

				# Check the pages_from value 
				if meta.name == "pages_from": 

					if passage_urn_low >= meta.value:
						if lt_pages_to:
							text_slug = text.slug
							break
						else:
							gt_pages_from = True

				# Check the pages_to value
				elif meta.name == "pages_to":

					if passage_urn_high <= meta.value:
						if gt_pages_from:
							text_slug = text.slug
							break
						else:
							lt_pages_to = True

			# Check an exact match on the chapter metadatum
			elif meta.name == "chapter":
				if meta.value == passage_urn[0]:
					text_slug = text.slug

	return text_slug 
