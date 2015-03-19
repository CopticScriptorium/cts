from django.shortcuts import get_object_or_404, redirect, render 
from django.http import HttpResponse
from texts.models import Text, Collection, SearchField, SearchFieldValue 
import pdb

def urn_redirect(request, query):
	"""
	Redirect the application to the correct text based on an ingested URN
	"""

	query = query.split("/")
	urn = query[0].split(":")
	col_urn = urn[3].split(".")
	collection_urn_code = col_urn[0] + "." + col_urn[1] 

	collection = get_object_or_404( Collection, urn_code=collection_urn_code )
		
	# If it's a xml query, for the moment redirect to github
	if query[-1] == "xml":
		return redirect( collection.github )

	if query[-1] == "reiannis":
		return redirect( collection.github )


	if len( urn ) > 4: 
		# It's a text query

		text_urn = urn[4] 
		url  = "/texts/" + text_urn

		if query[-1] == "html":
			url = url + "/"
			if query[-2] == "norm":
				url = url + "norm"
			elif query[-2] == "dipl":
				url = url + "dipl"
			elif query[-2] == "analytic":
				url = url + "analytic"
			elif query[-2] == "sahidica":
				url = url + "sahidica"

		return redirect( url ) 


	elif len( urn ) > 2:
		# It's a collection query, render the collection text index

		url = "/filter/corpus_urn=" + str( collection.id ) + ":" + collection.urn_code

		return redirect( url )

	else: 
		# Invalid URN
		return redirect( "/" )

