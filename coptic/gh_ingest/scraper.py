from django.db.models import Model
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from github3.exceptions import NotFoundError
from github3 import GitHub
from texts.models import Corpus

KNOWN_SLUGS = {
	"apophthegmata.patrum": "ap",
	"besa.letters": "besa_letters",
	"doc.papyri": "papyri",
	"johannes.canons": "johannes",
	"martyrdom.victor": "victor",
	"pseudo.theophilus": "pseudotheophilus",
	"sahidic.ot": "old-testament",
	"sahidica.1corinthians": "1st_corinthians",
	"sahidica.mark": "gospel_of_mark",
	"sahidica.nt": "new-testament",
	"shenoute.a22": "acephalous_work_22",
	"shenoute.abraham": "abraham_our_father",
	"shenoute.dirt": "shenoutedirt",
	"shenoute.eagerness": "eagernesss",
	"shenoute.fox": "not_because_a_fox_barks"
}

def get_setting_and_error_if_none(var_name, error_message):
	var = getattr(settings, var_name, None)
	if var is None:
		raise ImproperlyConfigured(error_message)
	return var


class CorpusNotFound(BaseException):
	"""Raised when the GithubCorpusScraper attempts to read a corpus that doesn't exist."""
	def __init__(self, corpus_slug, repo_owner, repo_name):
		repo = repo_owner + "/" + repo_name
		url = f"https://github.com/{repo}/tree/master"
		self.message = (f"Could not find corpus '{corpus_slug}' in {repo}."
						f"\n\tCheck {url} to make sure you spelled it correctly.")
		super().__init__(self, self.message)

	def __str__(self):
		return self.message


class EmptyCorpus(BaseException):
	"""Raised when a corpus exists but doesn't have directories ending in _TEI, _ANNIS, or _PAULA"""
	def __init__(self, corpus_slug, repo_owner, repo_name):
		repo = repo_owner + "/" + repo_name
		url = f"https://github.com/{repo}/tree/master"
		self.message = (f"Corpus '{corpus_slug}' doesn't appear to have any directories ending in "
						f"'_TEI', '_ANNIS', or '_PAULA'."
						f"\n\tCheck the contents of {url}.")
		super().__init__(self, self.message)

	def __str__(self):
		return self.message


class AmbiguousCorpus(BaseException):
	"""Raised when more than one dir ends with _TEI, _RELANNIS, or _PAULA"""
	def __init__(self, corpus_slug, repo_owner, repo_name):
		repo = repo_owner + "/" + repo_name
		url = f"https://github.com/{repo}/tree/master/{corpus_slug}"
		self.message = (f"Corpus '{corpus_slug}' has one or more directories that end with "
						f"_TEI, _ANNIS, or _PAULA."
						f"\n\tCheck the contents of {url} and remove the duplicate directories.")

	def __str__(self):
		return self.message


class InferenceError(BaseException):
	"""Raised when no known inference strategy works for recovering some piece of information."""
	def __init__(self, corpus_slug, repo_owner, repo_name, attr):
		repo = repo_owner + "/" + repo_name
		url = f"https://github.com/{repo}/tree/master/{corpus_slug}"
		self.message = (f"Failed to infer '{attr}' for '{corpus_slug}'. "
						f"\n\tCheck gh_ingest.scraper's implementation and either adjust the "
						f"corpus's structure or extend the scraper's inference strategies.")


class TTDirMissing(BaseException):
	"""Raised when the corpus's _TT directory is missing"""
	def __init__(self, corpus_slug, repo_owner, repo_name, tt_dir):
		repo = repo_owner + "/" + repo_name
		url = f"https://github.com/{repo}/tree/master/{corpus_slug}"
		self.message = (f"Could not find a _TT directory at {tt_dir} for corpus '{corpus_slug}'."
						f"\n\tCheck the contents of {url} and make sure there's a directory called {tt_dir}.")

	def __str__(self):
		return self.message


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

	def parse_corpora(self, corpus_dirnames):
		return [self.parse_corpus(corpus_dirname) for corpus_dirname in corpus_dirnames]

	def _infer_dir(self, corpus, dirs, *exts):
		target_dirs = []
		for ext in exts:
			if len(target_dirs) == 0:
				target_dirs = [x for x in dirs if x.lower().endswith(ext.lower())]
		if len(target_dirs) > 1:
			raise AmbiguousCorpus(corpus.slug, self.corpus_repo_owner, self.corpus_repo_name)
		return target_dirs[0] if len(target_dirs) == 1 else ''

	def _infer_annis_corpus_name(self, corpus):
		if corpus.github_tei != '':
			return corpus.github_tei[:corpus.github_tei.rfind("_")]
		elif corpus.github_relannis != '':
			return corpus.github_relannis[:corpus.github_relannis.rfind("_")]
		elif corpus.github_paula != '':
			return corpus.github_paula[:corpus.github_paula.rfind("_")]
		else:
			raise InferenceError(corpus.slug, self.corpus_repo_owner, self.corpus_repo_name, "annis_corpus_name")

	def _infer_slug(self, corpus):
		if corpus.annis_corpus_name in KNOWN_SLUGS:
			return KNOWN_SLUGS[corpus.annis_corpus_name]
		else:
			raise InferenceError(corpus.slug, self.corpus_repo_owner, self.corpus_repo_name, "slug")

	def parse_corpus(self, corpus_dirname):
		if corpus_dirname not in self._corpora:
			raise CorpusNotFound(corpus_dirname, self.corpus_repo_owner, self.corpus_repo_name)

		# TODO: special handling for bible

		# make a Corpus object and begin inferring its attributes
		corpus = Corpus()
		corpus.slug = corpus_dirname # provisionally, until we find the real one, so we can use this in errors
		corpus.github = f"https://github.com/{self.corpus_repo_owner}/{self.corpus_repo_name}/tree/master/{corpus_dirname}"

		dirs = [name for name, contents
				in self._repo.directory_contents(corpus_dirname)
				if contents.type == 'dir']
		corpus.github_tei = self._infer_dir(corpus, dirs, "_TEI")
		corpus.github_relannis = self._infer_dir(corpus, dirs, "_RELANNIS", "_ANNIS")
		corpus.github_paula = self._infer_dir(corpus, dirs, "_PAULA")
		if not any(str(x) and x != '' for x in [corpus.github_tei, corpus.github_paula, corpus.github_relannis]):
			raise EmptyCorpus(corpus_dirname, self.corpus_repo_owner, self.corpus_repo_name)

		corpus.annis_corpus_name = self._infer_annis_corpus_name(corpus)
		corpus.slug = self._infer_slug(corpus)

		tt_dir = corpus_dirname + "/" + corpus.annis_corpus_name + "_TT"
		try:
			texts = dict([(name, contents) for name, contents
						  in self._repo.directory_contents(tt_dir)])
		except NotFoundError as e:
			raise TTDirMissing(corpus_dirname, self.corpus_repo_owner, self.corpus_repo_name, tt_dir) from e

		print(Model.__repr__(corpus))




		# need to find out:
		# - title: Besa Letters
		# - urn_code: copticLit:besa

		# - html_visualization_formats

		# - slug: besa_letters
		# - annis_corpus_name: besa.letters
		# - github: https://github.com/CopticScriptorium/corpora/tree/master/besa-letters
		# - github_tei: besa.letters_TEI
		# - github_relannis: besa.letters_ANNIS
		# - github_paula: besa.letters_PAULA








