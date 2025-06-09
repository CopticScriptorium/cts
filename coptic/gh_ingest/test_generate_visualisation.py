import os
import unittest
from gh_ingest.htmlvis import generate_visualization

class TestHtmlVis(unittest.TestCase):

    def read_file(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()

    def test_generate_visualization(self):
        return # Skip this test for now - we need to update the logic to texts.get(), self.config, self.visualization_format_slug
    
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        base_path = os.path.join(BASE_DIR, 'coptic/gh_ingest/docs/example')
        
        sgml_file = os.path.join(base_path, 'pilate.1643.27-28.tt')
        expected_output_file = os.path.join(base_path, 'pilate.1643.27-28.diplomatic.html')

        sgml_content = self.read_file(sgml_file)
        expected_output = self.read_file(expected_output_file)

        generated_output = generate_visualization("dipl", sgml_content)
        self.maxDiff=None
        self.assertEqual(generated_output.strip()[0:4000], expected_output.strip()[0:4000], "Generated output does not match expected output")

if __name__ == "__main__":

    unittest.main()