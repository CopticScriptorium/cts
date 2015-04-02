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

		# Add the text URN slug 
		text_urn = urn[5] 
		url  = "/texts/" + text_urn

		# If it's an HTML query, specify redirect to the html visualization url 
		if query[-1] == "html":
			url = url + "/" + query[-2]

		return redirect( url ) 

	# If it's a length of 5, this means the URN might be a text or might be a manuscript
	elif len( urn ) == 5: 

		possible_text_urn = urn[4] 
		texts = Text.objects.filter(slug=possible_text_urn)

		# A text exists for the URN query parameter 
		if len( texts ):

			# Add the text URN slug
			url  = "/texts/" + texts[0].slug

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


	# Else, it's an inv
	else: 
		# Invalid URN
		return redirect( "/" )

