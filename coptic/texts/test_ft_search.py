import unittest
from bs4 import BeautifulSoup
from texts.ft_search import Search

class TestSearch(unittest.TestCase):
    def setUp(self):
        self.search = Search()


if __name__ == '__main__':
    unittest.main()