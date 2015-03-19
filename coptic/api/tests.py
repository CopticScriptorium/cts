from django.test import TestCase

class ApiViewsTestCase(TestCase):
	def test_api_view(self):
		print(" -- testing API views")
		resp = self.client.get("/api/")
		self.assertEqual(resp.status_code, 200)