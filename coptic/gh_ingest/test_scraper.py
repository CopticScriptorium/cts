import os
import unittest
from unittest.mock import patch, MagicMock
from django.conf import settings
from django.test import override_settings, TestCase
from gh_ingest.scraper import LocalCorpusScraper, LocalEmptyCorpus, LocalTTDirMissing, LocalNoTexts

class TestLocalCorpusScraper(unittest.TestCase):
    
    @patch('os.listdir')
    @patch('os.path.isdir')
    @patch('gh_ingest.scraper.get_setting_and_error_if_none')
    def test_infer_local_dirs(self, mock_get_setting, mock_isdir, mock_listdir):
        # Setup mock return values
        mock_get_setting.return_value = '/mock/local/repo/path'
        mock_listdir.return_value = [
            'pseudo.timothy_ANNIS', 'pseudo.timothy_CONLLU', 'pseudo.timothy_PAULA', 'pseudo.timothy_TEI'
        ]
        mock_isdir.side_effect = lambda path: not path.endswith('.zip')
        
        scraper = LocalCorpusScraper()
        corpus = MagicMock()
        
        # Call the method
        result = scraper._infer_local_dirs(corpus, 'pseudo-timothy')
        
        # Check the results
        self.assertEqual(result, ('pseudo.timothy_TEI', 'pseudo.timothy_ANNIS', 'pseudo.timothy_PAULA'))

    @patch('os.listdir')
    @patch('os.path.isdir')
    @patch('gh_ingest.scraper.get_setting_and_error_if_none')
    def test_infer_local_dirs_empty_corpus(self, mock_get_setting, mock_isdir, mock_listdir):
        # Setup mock return values
        mock_get_setting.return_value = '/mock/local/repo/path'
        mock_listdir.return_value = []
        mock_isdir.side_effect = lambda path: not path.endswith('.zip')
        
        scraper = LocalCorpusScraper()
        corpus = MagicMock()
        
        # Call the method and check for LocalEmptyCorpus exception
        with self.assertRaises(LocalEmptyCorpus):
            scraper._infer_local_dirs(corpus, 'empty-corpus')

@override_settings(LOCAL_REPO_PATH='../../corpora')
class TestLocalCorpusScraperWithFiles(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.local_repo_path = settings.LOCAL_REPO_PATH
        cls.scraper = LocalCorpusScraper()

    def test_infer_local_dirs(self):
        corpus_dirname = 'pseudo-timothy'
        corpus = MagicMock()
        result = self.scraper._infer_local_dirs(corpus, corpus_dirname)
        self.assertEqual(result, ('pseudo.timothy_TEI', 'pseudo.timothy_ANNIS', 'pseudo.timothy_PAULA'))

    def test_get_texts(self):
        corpus_dirname = 'pseudo-timothy'
        corpus = MagicMock()
        corpus.github_paula = 'pseudo.timothy_PAULA'
        corpus.annis_corpus_name = 'pseudo.timothy'
        texts = self.scraper._get_texts(corpus, corpus_dirname)
        self.assertTrue(len(texts) > 0)

    def test_get_texts_no_texts(self):
        corpus_dirname = 'empty-corpus'
        corpus = MagicMock()
        corpus.github_paula = 'empty-corpus_PAULA'
        corpus.annis_corpus_name = 'empty-corpus'
        with self.assertRaises(LocalTTDirMissing):
            self.scraper._get_texts(corpus, corpus_dirname)

    def test_get_texts_missing_dir(self):
        corpus_dirname = 'nonexistent-corpus'
        corpus = MagicMock()
        corpus.github_paula = 'nonexistent-corpus_PAULA.zip'
        corpus.annis_corpus_name = 'nonexistent-corpus'
        with self.assertRaises(LocalTTDirMissing):
            self.scraper._get_texts(corpus, corpus_dirname)

    def test_infer_urn_code(self):
        corpus_dirname = 'pseudo-timothy'
        self.scraper._latest_meta_dict = {"document_cts_urn": "urn:cts:copticLit:pseudo.timothy"}
        urn_code = self.scraper._infer_urn_code(corpus_dirname)
        self.assertEqual(urn_code, "urn:cts:copticLit:pseudo")

    def test_parse_corpus(self):
        corpus_dirname = 'pseudo-timothy'
        transaction = self.scraper.parse_corpus(corpus_dirname)
        self.assertIsNotNone(transaction)
        self.assertTrue(len(transaction._text_pairs) > 0)

if __name__ == '__main__':
    unittest.main()