import unittest
from bs4 import BeautifulSoup
from texts.ft_search import Search

class TestSearch(unittest.TestCase):
    def setUp(self):
        self.search = Search()

    def test_reduce_text_with_ellipsis_no_highlight(self):
        html_text = "<p>This is a test sentence without any highlights.</p>"
        expected_output = "This is a test sentence without any highlights."
        result = self.search.reduce_text_with_ellipsis(html_text, 2)
        self.assertEqual(result, expected_output)

    def test_reduce_text_with_ellipsis_single_highlight(self):
        html_text = '<p>This is a very good <span class="highlight">test</span> case with a sentence with a highlight.</p>'
        expected_output = 'This is a [...] very good <span class="highlight">test</span> case with [...] with a highlight.'
        result = self.search.reduce_text_with_ellipsis(html_text, 2)
        self.assertEqual(result, expected_output)

    def test_reduce_text_with_ellipsis_multiple_highlights(self):
        html_text = '<p>This is a <span class="highlight">test</span> sentence with <span class="highlight">multiple</span> highlights.</p>'
        expected_output = 'This is a [...] is a <span class="highlight">test</span> sentence with [...] sentence with <span class="highlight">multiple</span> highlights.'
        result = self.search.reduce_text_with_ellipsis(html_text, 2)
        self.assertEqual(result, expected_output)
        
    def test_reduce_text_with_ellipsis_multiple_highlights_and_long_segments(self):
        html_text = 'Beginning: This is a long sentence with a lots of words and such <span class="highlight">test</span> another long sentence with a lots of words and such This is a long sentence with a lots of words and such This is a <span class="highlight">second</span> long sentence with a lots of words and such  <span class="highlight">multiple</span> highlights. This is a long sentence with a lots of words and such This is a long sentence with a lots of words and such This is a long sentence with a lots of words and such. This is the end.'
        expected_output = 'Beginning: This is [...] and such <span class="highlight">test</span> another long [...] is a <span class="highlight">second</span> long sentence [...] and such <span class="highlight">multiple</span> highlights. This [...] is the end.'
        result = self.search.reduce_text_with_ellipsis(html_text, 2)
        self.assertEqual(result, expected_output)

    def test_reduce_text_with_ellipsis_context(self):
        html_text = '<p>This is a <span class="highlight">test</span> sentence with a highlight.</p>'
        expected_output = 'This is a [...] a <span class="highlight">test</span> sentence [...] with a highlight.'
        result = self.search.reduce_text_with_ellipsis(html_text, context_size=1)
        self.assertEqual(result, expected_output)

    def test_reduce_text_with_ellipsis_no_match(self):
        html_text = '<p>This is a <span class="highlight">test</span> sentence with a highlight.</p>'
        expected_output = '<span class="highlight">test</span>'
        result = self.search.reduce_text_with_ellipsis(html_text, context_size=0)
        self.assertEqual(result, expected_output)

if __name__ == '__main__':
    unittest.main()