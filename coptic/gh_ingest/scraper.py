from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from github3 import GitHub


def get_setting_and_error_if_none(var_name, error_message):
	var = getattr(settings, var_name, None)
	if var is None:
		raise ImproperlyConfigured(error_message)
	return var


class CorpusNotFound(BaseException):
	"""Raised when the GithubCorpusScraper attempts to read a corpus that doesn't exist."""
	def __init__(self, corpus_name, repo_owner, repo_name):
		self.corpus_name = corpus_name
		self.repo = repo_owner + "/" + repo_name


class ScrapedCorpus:

	def __init__(self):
		pass


class GithubCorpusScraper:

	def __init__(self):
		corpus_repo_owner = get_setting_and_error_if_none(
			"CORPUS_REPO_OWNER",
			"A corpus repository owner must be specified, e.g. 'CopticScriptorium' if the "
			"URL is https://github.com/CopticScriptorium/corpora"
		)
		corpus_repo_name = get_setting_and_error_if_none(
			"CORPUS_REPO_NAME",
			"A corpus repository name must be specified, e.g. 'corpora' if the "
			"URL is https://github.com/CopticScriptorium/corpora"
		)
		self.corpus_repo_owner = corpus_repo_owner
		self.corpus_repo_name = corpus_repo_name

		self._repo = GitHub().repository(corpus_repo_owner, corpus_repo_name)
		self._corpora = dict(self._repo.directory_contents(""))

	def parse_corpora(self, corpus_names):
		return [self.parse_corpus(corpus_name) for corpus_name in corpus_names]

	def parse_corpus(self, corpus_name):
		if corpus_name not in self._corpora:
			raise CorpusNotFound(corpus_name, self.corpus_repo_owner, self.corpus_repo_name)

		dirs = [name for name, contents
				in self._repo.directory_contents(corpus_name)
				if contents.type == 'dir']
		print(dirs)






