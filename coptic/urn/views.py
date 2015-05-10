import logging
from django.shortcuts import get_object_or_404, redirect, render 
from django.http import HttpResponse
from texts.models import Text, Corpus, SearchField, SearchFieldValue 

def urn_redirect(request, query):
	"""
	Redirect the application to the correct text based on an ingested URN
	"""

	# Set up an instance of the logger
	logger = logging.getLogger(__name__)

	# Split the initial URN query parameters
	query = query.split("/")
	urn_candidate = query[0].split(":")

	# If the URN colon separated values length is greater than or equal to 4 
	# (e.g. urn:cts:copticLit:shenoute..etc. ) 
	if len( urn_candidate ) >= 4:

		# Take the 4th item in the urn_candidate string like the text URN to divide to textgroup,
		# work, and passage parameters 
		text_urn = urn_candidate[3].split(".")

		# If the text_urn length is greater than or equal to a length of 3, treat it like a passage URN
		if len( text_urn ) >= 3:

			# reconstruct the corpus urn 
			corpus_urn = text_urn[0] + "." + text_urn[1] 

			# Check the passage URN against the corpus texts metadata
			text = check_passage_urn( urn_candidate )

			# A text exists for the URN query parameter 
			if text:
				# Add the slug to the redirect URL  
				url  = "/texts/" + text.corpus.slug + "/" + text.slug 

				# If it's an HTML query, specify redirect to the html visualization url 
				if query[-1] == "html":
					url = url + "/" + query[-2]

				# If it's a xml query, for the moment redirect to github
				elif query[-1] == "xml":
					return redirect( text.corpus.github )

				# If it's an REI annis query, redirect to github
				elif query[-1] == "relannis":
					return redirect( text.corpus.github )

				# If it's an ANNIS URN, redirect to ANNIS
				elif query[-1] == "annis":
					return redirect( "https://corpling.uis.georgetown.edu/annis/scriptorium#_c=" + text.corpus.annis_code )	

				# Redirect to the specified text passage url
				return redirect( url )

			else:
				# Invalid URN
				# In the future, add URN not found error notice
				logger.error( " -- URN error, no passage slug found from check_passage_urn")
				return redirect( "/" )


		# If the text_urn length is equal to 2, treat it like a corpus urn
		elif len( text_urn ) == 2:

			# Reconstruct the corpus/work/corpus urn
			corpus_urn = text_urn[0] + "." + text_urn[1] 

			# Add the corpus urn filter 
			url = "/filter/corpus_urn=0:" + corpus_urn

			# Redirect to the specified URL 
			return redirect( url )

		# If the text_urn length is equal to 1, treat it like a textgroup
		elif len( text_urn ) == 1:

			# Set the base textgroup URN
			textgroup_urn = text_urn[0]

			# Set the textgroup urn filter
			url = "/filter/textgroup_urn=0:" + textgroup_urn

			# Redirect to the specified URL 
			return redirect( url )

		# Else, it's an invalid URN
		else:
			# Invalid URN
			# In the future, add URN not found error notice
			logger.error( " -- URN error, no textgroup, work, or passage URN to query" )
			return redirect( "/" )


	# Else, it's an invalid URN
	else: 
		# Invalid URN
		# In the future, add URN not found error notice
		logger.error( " -- URN error, malformed URN for colon demarcated parameters" )
		return redirect( "/" )


def check_passage_urn( urn_candidate ):
	"""
	Lookup the passage URN against the document_cts_urn metadata from ANNIS
	"""
	sel_text = {}

	# Check the passage urn against each text metadata
	for text in Text.objects.all(): 

		# For each meta item, check if it is pages_from, pages_to, or chapter
		for meta in text.text_meta.all():

			# Check the pages_from / pages_to range against the passage_urn
			if meta.name == "document_cts_urn":
				if meta.value.split(":")[3] == urn_candidate[3]: 
					sel_text = text	

	return sel_text 