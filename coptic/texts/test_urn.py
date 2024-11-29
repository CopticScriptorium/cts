import sys
import os
import unittest

# Add the directory containing urn.py to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from urn import cts_work, textgroup_urn, corpus_urn, parts, partial_parts_match

class TestURNFunctions(unittest.TestCase):

    def test_cts_work(self):
        self.assertEqual(cts_work("urn:cts:copticLit:psathanasius.matthew20.budge:1:56"), "urn:cts:copticLit")
        self.assertEqual(cts_work("urn:cts:greekLit:tlg0012.tlg001:1.1"), "urn:cts:greekLit")

    def test_textgroup_urn(self):
        self.assertEqual(textgroup_urn("urn:cts:copticLit:psathanasius.matthew20.budge:1:56"), "urn:cts:copticLit:psathanasius")
        self.assertEqual(textgroup_urn("urn:cts:greekLit:tlg0012.tlg001:1.1"), "urn:cts:greekLit:tlg0012")

    def test_corpus_urn(self):
        self.assertEqual(corpus_urn("urn:cts:copticLit:psathanasius.matthew20.budge:1:56"), "urn:cts:copticLit:psathanasius.matthew20")
        self.assertEqual(corpus_urn("urn:cts:greekLit:tlg0012.tlg001:1.1"), "urn:cts:greekLit:tlg0012.tlg001")

    def test_parts(self):
        self.assertEqual(parts("urn:cts:copticLit:psathanasius.matthew20.budge:1:56"), ['urn', 'cts', 'copticLit', 'psathanasius', 'matthew20', 'budge', '1', '56'])
        self.assertEqual(parts("urn:cts:greekLit:tlg0012.tlg001:1.1"), ['urn', 'cts', 'greekLit', 'tlg0012', 'tlg001', '1', '1'])

    def test_partial_parts_match(self):
        self.assertTrue(partial_parts_match("urn:cts:copticLit:psathanasius.matthew20.budge:1:56", "urn:cts:copticLit:psathanasius.matthew20"))
        self.assertFalse(partial_parts_match("urn:cts:copticLit:psathanasius.matthew20.budge:1:56", "urn:cts:greekLit:tlg0012.tlg001:1.1"))
        self.assertTrue(partial_parts_match("urn:cts:copticLit:psathanasius.matthew20.budge:1:56", "urn:cts:copticLit:psathanasius.matthew20.budge"))

if __name__ == '__main__':
    unittest.main()