from django.test import TestCase

class TextViewsTestCase(TestCase):
	def test_text_view(self):
		print(" -- testing the text views")
		resp = self.client.get("/texts/ya421-428/")
		self.assertEqual(resp.status_code, 200)