import requests


def github_directories_exist(corpus):
	'Returns a sequence of booleans indicating whether each of the three github subdirectories are present for the corpus'

	def subdir_found(part):
		url = '%s/%s_%s' % (corpus.github, corpus.annis_corpus_name, part)
		resp = requests.get(url)
		return resp.status_code == 200

	return tuple((subdir_found(part) for part in ('TEI', 'relANNIS', 'PAULA')))
