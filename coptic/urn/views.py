import logging
from base64 import b64encode
from django.shortcuts import redirect


def urn_redirect(request, query):
	"""
	Redirect the application to the correct text based on an ingested URN
	"""

	logger = logging.getLogger(__name__)

	query = query.split("/")
	urn_candidate = query[0].split(":")

	if len(urn_candidate) >= 4:  # e.g. ['', 'cts', 'copticLit', 'shenoute']

		# Take the 4th item in the urn_candidate string like the text URN to divide to textgroup,
		# work, and passage parameters 
		text_urn = urn_candidate[3].split(".")

		if len(text_urn) >= 3:  # passage URN

			# reconstruct the corpus urn 
			corpus_urn = '.'.join(text_urn[:2])

			# Check the passage URN against the corpus texts metadata
			text = passage_text(urn_candidate[3])

			# A text exists for the URN query parameter 
			if text:
				# Add the slug to the redirect URL  
				url = "/texts/" + text.corpus.slug + "/" + text.slug

				if query[-1] == "html":  # redirect to the html visualization url
					url = url + "/" + query[-2]

				elif query[-1] == "xml":  # For the moment, redirect to github
					return redirect(text.corpus.github)

				# If it's an REI annis query, redirect to github
				elif query[-1] == "relannis":
					return redirect(text.corpus.github)

				elif query[-1] == "annis":
					return redirect("https://corpling.uis.georgetown.edu/annis/scriptorium#_c=" +
							b64encode(text.corpus.urn_code))

				# Redirect to the specified text passage url
				return redirect(url)

			else:
				logger.error(" -- URN error, no passage slug found from check_passage_urn")
				return redirect("/")

		elif len(text_urn) == 2:  # corpus urn
			return redirect("/filter/corpus_urn=0:" + '.'.join(text_urn))

		elif len(text_urn) == 1:  # textgroup
			return redirect("/filter/textgroup_urn=0:" + text_urn[0])

		else:
			logger.error(" -- URN error, no textgroup, work, or passage URN to query")
			return redirect("/")

	else:
		logger.error(" -- URN error, malformed URN for colon demarcated parameters")
		return redirect("/")


def passage_text(passage):
	"""
	Look up the passage URN against the document_cts_urn metadatum from ANNIS
	"""

	# Check the passage urn against each text metadatum
	for text in Text.objects.all(): 
		for meta in text.text_meta.filter(name = 'document_cts_urn'):
			if meta.value.split(":")[3] == passage:
				return text
