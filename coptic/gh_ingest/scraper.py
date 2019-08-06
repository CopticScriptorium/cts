import re

from django.db.models import Model
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import transaction
from django.utils.text import slugify
from github3.exceptions import NotFoundError
from github3 import GitHub

from texts.models import Corpus, Text, TextMeta

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


class CorpusTransaction:
	"""Keeps track of every object that needs to be added to the SQL database for a given corpus,
	and atomically saves all of them."""

	def __init__(self, corpus_name, corpus):
		self.corpus_name = corpus_name
		self._corpus = corpus
		self._text_pairs = []

	def add_text(self, text_pair):
		self._text_pairs.append(text_pair)

	@transaction.atomic
	def execute(self):

		self._corpus.save()

		for text, text_metas in self._text_pairs:
			# save all the metas
			for text_meta in text_metas:
				text_meta.save()

			# get rid of corpus temporarily...
			corpus = text.corpus
			text.corpus = None
			text.save()

			# then write it once we've gotten an ID for the text
			text.corpus = corpus
			text.save()

			# now add all the metas and save again
			for text_meta in text_metas:
				text.text_meta.add(text_meta)
			text.save()

		return {"texts": len(self._text_pairs),
				"text_metas": sum(map(lambda x: len(x[1]), self._text_pairs))}


class ScraperException(BaseException):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)


class CorpusNotFound(ScraperException):
	"""Raised when the GithubCorpusScraper attempts to read a corpus that doesn't exist."""
	def __init__(self, corpus_dirname, repo_owner, repo_name):
		repo = repo_owner + "/" + repo_name
		url = f"https://github.com/{repo}/tree/master"
		self.message = (f"Could not find corpus '{corpus_dirname}' in {repo}."
						f"\n\tCheck {url} to make sure you spelled it correctly.")
		super().__init__(self, self.message)

	def __str__(self):
		return self.message


class EmptyCorpus(ScraperException):
	"""Raised when a corpus exists but doesn't have directories ending in _TEI, _ANNIS, or _PAULA"""
	def __init__(self, corpus_dirname, repo_owner, repo_name):
		repo = repo_owner + "/" + repo_name
		url = f"https://github.com/{repo}/tree/master"
		self.message = (f"Corpus '{corpus_dirname}' doesn't appear to have any directories ending in "
						f"'_TEI', '_ANNIS', or '_PAULA'."
						f"\n\tCheck the contents of {url}.")
		super().__init__(self, self.message)

	def __str__(self):
		return self.message


class AmbiguousCorpus(ScraperException):
	"""Raised when more than one dir ends with _TEI, _RELANNIS, or _PAULA"""
	def __init__(self, corpus_dirname, repo_owner, repo_name):
		repo = repo_owner + "/" + repo_name
		url = f"https://github.com/{repo}/tree/master/{corpus_dirname}"
		self.message = (f"Corpus '{corpus_dirname}' has one or more directories that end with "
						f"_TEI, _ANNIS, or _PAULA."
						f"\n\tCheck the contents of {url} and remove the duplicate directories.")

	def __str__(self):
		return self.message


class InferenceError(ScraperException):
	"""Raised when no known inference strategy works for recovering some piece of information."""
	def __init__(self, corpus_dirname, repo_owner, repo_name, attr):
		repo = repo_owner + "/" + repo_name
		url = f"https://github.com/{repo}/tree/master/{corpus_dirname}"
		self.message = (f"Failed to infer '{attr}' for '{corpus_dirname}'. "
						f"\n\tCheck gh_ingest.scraper's implementation and either adjust the "
						f"corpus's structure or extend the scraper's inference strategies.")


class TTDirMissing(ScraperException):
	"""Raised when the corpus's _TT directory is missing"""
	def __init__(self, corpus_dirname, repo_owner, repo_name, tt_dir):
		repo = repo_owner + "/" + repo_name
		url = f"https://github.com/{repo}/tree/master/{corpus_dirname}"
		self.message = (f"Could not find a _TT directory at {tt_dir} for corpus '{corpus_dirname}'."
						f"\n\tCheck the contents of {url} and make sure there's a directory called {tt_dir}.")

	def __str__(self):
		return self.message


class NoTexts(ScraperException):
	"""Raised when a corpus has no texts"""
	def __init__(self, corpus_dirname, repo_owner, repo_name, tt_dir):
		repo = repo_owner + "/" + repo_name
		url = f"https://github.com/{repo}/tree/master/{corpus_dirname}/{tt_dir}"
		self.message = (f"Found a _TT directory at {tt_dir} for corpus '{corpus_dirname}', but it is empty."
						f"\n\tCheck the contents of {url} and make sure it has some texts.")

	def __str__(self):
		return self.message


class MetaNotFound(ScraperException):
	"""Raised when text metadata couldn't be found"""
	def __init__(self, repo_owner, repo_name, file_path):
		repo = repo_owner + "/" + repo_name
		url = f"https://github.com/{repo}/tree/master/{file_path}"
		self.message = (f"Could not find metadata in text '{file_path}'."
						f"\n\tCheck the contents of {url} and make sure the text has a <meta> element.")

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

		self._repo = GitHub(
			username=getattr(settings, "GITHUB_USERNAME", ""),
			password=getattr(settings, "GITHUB_PASSWORD", "")
		).repository(corpus_repo_owner, corpus_repo_name)
		self._corpora = dict(self._repo.directory_contents(""))  # name -> github3.py contents object

		### stateful member variables that contain information related to the corpus currently being processed
		# the texts.models.Corpus object corresponding to the corpus being processed
		self._current_corpus = None
		# a CorpusTransaction, i.e. a per-corpus list of objects we need to save
		self._current_transaction = None
		# the github3.py contents object of the most recently seen text
		self._current_text_contents = None
		# the metadata dictionary of the most recently seen text
		self._latest_meta_dict = None

	# corpus-level methods ---------------------------------------------------------------------------------------------

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

	def _infer_github_dirs(self, corpus, corpus_dirname):
		dirs = [name for name, contents
				in self._repo.directory_contents(corpus_dirname)
				if contents.type == 'dir']
		corpus.github_tei = self._infer_dir(corpus, dirs, "_TEI")
		corpus.github_relannis = self._infer_dir(corpus, dirs, "_RELANNIS", "_ANNIS")
		corpus.github_paula = self._infer_dir(corpus, dirs, "_PAULA")
		if not any(str(x) and x != '' for x in [corpus.github_tei, corpus.github_paula, corpus.github_relannis]):
			raise EmptyCorpus(corpus_dirname, self.corpus_repo_owner, self.corpus_repo_name)

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

	def _get_texts(self, corpus, corpus_dirname):
		tt_dir = corpus_dirname + "/" + corpus.annis_corpus_name + "_TT"
		try:
			texts = [(name, contents) for name, contents
					 in self._repo.directory_contents(tt_dir)]
		except NotFoundError as e:
			raise TTDirMissing(corpus_dirname, self.corpus_repo_owner, self.corpus_repo_name, tt_dir) from e
		if len(texts) == 0:
			raise NoTexts(corpus_dirname, self.corpus_repo_owner, self.corpus_repo_name, tt_dir)

		return dict(texts)

	def _infer_urn_code(self, corpus_dirname):
		meta = self._latest_meta_dict
		if meta is None or "document_cts_urn" not in meta:
			raise InferenceError(corpus_dirname, self.corpus_repo_owner, self.corpus_repo_name, "urn_code")

		doc_urn = meta["document_cts_urn"].split(":")
		corpus_urn = ":".join(doc_urn[2:4])
		if corpus_urn == "":
			raise InferenceError(corpus_dirname, self.corpus_repo_owner, self.corpus_repo_name, "urn_code")

		return corpus_urn

	def parse_corpus(self, corpus_dirname):
		if corpus_dirname not in self._corpora:
			raise CorpusNotFound(corpus_dirname, self.corpus_repo_owner, self.corpus_repo_name)

		# TODO: special handling for bible

		# make a Corpus object and begin inferring its attributes
		corpus = Corpus()
		self._current_corpus = corpus
		# All objects we make will go into this list
		self._current_transaction = CorpusTransaction(corpus_dirname, corpus)

		corpus.slug = corpus_dirname # provisionally, until we find the real one, so we can use this in errors
		corpus.github = f"https://github.com/{self.corpus_repo_owner}/{self.corpus_repo_name}/tree/master/{corpus_dirname}"
		self._infer_github_dirs(corpus, corpus_dirname)
		corpus.annis_corpus_name = self._infer_annis_corpus_name(corpus)
		corpus.slug = self._infer_slug(corpus)
		# This is the best we can do, since a human readable version is not available.
		corpus.title = corpus.annis_corpus_name

		texts = self._get_texts(corpus, corpus_dirname)
		self._scrape_texts_and_add_to_tx(texts)  # side effect: this will add more objects to self._current_transaction

		corpus.urn_code = self._infer_urn_code(corpus_dirname)

		return self._current_transaction

	# - html_visualization_formats

	# text-level methods -----------------------------------------------------------------------------------------------

	def _scrape_texts_and_add_to_tx(self, texts):
		for contents in texts.values():
			self._current_text_contents = contents
			self._scrape_text_and_add_to_tx(contents)

	def _get_meta_dict(self, tt_lines):
		for line in tt_lines:
			if line.startswith('<meta'):
				return dict(re.findall(r'(?P<attr>\w+)="(?P<value>.*?)"', line))
		raise MetaNotFound(self.corpus_repo_owner, self.corpus_repo_name, self._current_text_contents.path)

	def _scrape_text_and_add_to_tx(self, contents):
		contents.refresh()
		tt_lines = contents.decoded.decode('utf-8').split("\n")

		meta = self._get_meta_dict(tt_lines)
		self._latest_meta_dict = meta

		text = Text()
		text.title = meta["title"]
		text.slug = slugify(meta["title"])
		text.corpus = self._current_corpus

		text_metas = [TextMeta(name=name, value=value) for name, value in meta.items()]

		self._current_transaction.add_text((text, text_metas))








