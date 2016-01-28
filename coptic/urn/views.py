import logging
from django.shortcuts import redirect

logger = logging.getLogger(__name__)


def urn_redirect(request, query):
	'Redirect to the correct place based on a URN'
	value = urn_redirect_value(query)
	logger.info('Redirecting to %s from %s' % (value, query))
	return redirect(value)


def urn_redirect_value(query):

	query_split_by_slash = query.split("/")
	query_tail = query_split_by_slash[-1]
	urn_candidate = query_split_by_slash[0].split(":")

	if len(urn_candidate) == 5:  # passage URN
		# reconstruct the corpus urn
		corpus_urn = urn_candidate[3]

		# Check the passage URN against the corpus texts metadata
		text = passage_text(urn_candidate[3])

		# A text exists for the URN query parameter
		if text:
			# Add the slug to the redirect URL
			url = "/texts/" + text.corpus.slug + "/" + text.slug

			if query_tail == "html":  # redirect to the html visualization url
				url = url + "/" + query_split_by_slash[-2]

			# Redirect to the specified text passage url
			return url
		else:
			logger.error(" -- URN error, no passage slug found from check_passage_urn")
			return "/"

	elif len(urn_candidate) >= 4:  # e.g. ['', 'cts', 'copticLit', 'shenoute']
		# Take the 4th item in the urn_candidate string like the text URN to divide to textgroup,
		# work, and passage parameters



		text_urn = urn_candidate[3].split(".")

		if len(text_urn) == 2:  # corpus urn
			return "/filter/corpus_urn=0:" + '.'.join(text_urn)

		elif len(text_urn) == 1:  # textgroup
			return "/filter/textgroup_urn=0:" + text_urn[0]

		else:
			logger.error(" -- URN error, no textgroup, work, or passage URN to query")
			return "/"

	else:
		logger.error(" -- URN error, malformed URN for colon demarcated parameters")
		return "/"


def passage_text(passage):
	"""
	Look up the passage URN against the document_cts_urn metadatum from ANNIS
	"""

	# Check the passage urn against each text metadatum
	for text in Text.objects.all(): 
		for meta in text.text_meta.filter(name = 'document_cts_urn'):
			if meta.value.split(":")[3] == passage:
				return text


import unittest

class ViewsTest(unittest.TestCase):
	def run_and_assert(self, input, expected):
		self.assertEqual(urn_redirect_value(input), expected)

	def test_corpus_urn(self):
		self.run_and_assert('urn:cts:copticLit:shenoute.fox', '/filter/corpus_urn=0:shenoute.fox')

	def test_a(self):
		self.run_and_assert('urn:cts:copticLit:nt.mark.sahidica_ed:1', '?')

	def test_a2(self):
		self.run_and_assert('urn:cts:copticLit:nt.mark.sahidica_ed', '?')

	def test_a3(self):
		self.run_and_assert('urn:cts:copticLit:nt.mark', '?')

	def test_a4(self):
		self.run_and_assert('urn:cts:copticLit:nt', '?')

	def test_a5(self):
		self.run_and_assert('urn:cts:copticLit', '?')

	def test_a6(self):
		self.run_and_assert('urn:cts', '?')

	def test_b(self):
		self.run_and_assert('urn:cts:copticLit:shenoute.abraham.monbxl_93_94', '?')

	def test_garbage_returns_slash(self):
		self.run_and_assert('garbage', '/')

if __name__ == '__main__':
	unittest.main()
