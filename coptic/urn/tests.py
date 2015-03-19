from django.test import TestCase

class UrnViewsTestCase(TestCase):
	def urn_text_view(self):
		print(" -- testing the urn views")
		resp = self.client.get("/urn:cts:copticLit:shenoute.A22")
		self.assertEqual(resp.status_code, 301)