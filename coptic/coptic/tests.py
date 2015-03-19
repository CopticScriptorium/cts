from django.test import TestCase

class CopticViewsTestCase(TestCase):
	def test_coptic_view(self):
		print(" -- testing Coptic views")
		resp = self.client.get("/")
		self.assertEqual(resp.status_code, 200)