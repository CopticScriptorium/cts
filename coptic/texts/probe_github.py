import requests
import json


def github_directory_names(corpus):
	'Return a sequence of directory names or blanks'

	# Get the Github API URL for the contents of the corpus page
	url = 'https://api.github.com/repos/CopticScriptorium/corpora/contents/' + corpus.github.split('/')[-1]
	resp = requests.get(url)

	# Decode the JSON into a list of items (files, directories, etc.)
	dir_contents_list = json.loads(resp.text)

	# Extract directory names for this corpus
	dir_names = [item['name'] for item in dir_contents_list if item['type'] == 'dir' and item['name'].
		startswith(corpus.annis_corpus_name)]

	def dir_name_or_blank(category):
		'Search the directory names for one of TEI, etc., and return that name, or an empty string.'
		matches = [dir_name for dir_name in dir_names if category in dir_name]
		return matches[0] if matches else ''

	# Get the directory name or '' for each of the categories
	ordered_dir_names = tuple((dir_name_or_blank(category) for category in ('TEI', 'ANNIS', 'PAULA')))

	return ordered_dir_names
