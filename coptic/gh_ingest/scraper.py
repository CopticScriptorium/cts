import re

from django.db.models import Model
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import transaction
from django.utils.text import slugify
from github3.exceptions import NotFoundError
from github3 import GitHub

from texts.models import Corpus, Text, TextMeta, HtmlVisualization, HtmlVisualizationFormat
from .scraper_exceptions import *

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
		self._vis_formats = []

	def add_text(self, text_pair):
		self._text_pairs.append(text_pair)

	def add_vis_formats(self, formats):
		self._vis_formats = formats

	@transaction.atomic
	def execute(self):
		self._corpus.save()
		self._corpus.html_visualization_formats.set(self._vis_formats)
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

		# the 5 known visualization formats
		self._known_visualization_formats = HtmlVisualizationFormat.objects.all().values_list('button_title', flat=True)
		# a map from the visualization subtype (identical to a val of HtmlVisualizationFormat's button_title field)
		# to the file in ExtData that contains information about it
		self._vis_configs = {}

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
		github_tei = self._infer_dir(corpus, dirs, "_TEI")
		github_relannis = self._infer_dir(corpus, dirs, "_RELANNIS", "_ANNIS")
		github_paula = self._infer_dir(corpus, dirs, "_PAULA")
		if not any(str(x) and x != '' for x in [github_tei, github_paula, github_relannis]):
			raise EmptyCorpus(corpus_dirname, self.corpus_repo_owner, self.corpus_repo_name)
		return github_tei, github_relannis, github_paula

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
		corpus_urn = doc_urn[2] + ":" + doc_urn[3].split(".")[0]
		if corpus_urn == "":
			raise InferenceError(corpus_dirname, self.corpus_repo_owner, self.corpus_repo_name, "urn_code")

		return corpus_urn

	def _parse_resolver_vis_map(self, text, corpus, corpus_dirname):
		lines = text.strip().split("\n")
		lines = [line.split("\t") for line in lines]
		if not all(len(line) == 9 for line in lines):
			raise ResolverVisMapIssue(
				corpus_dirname,
				self.corpus_repo_owner,
				self.corpus_repo_name,
				corpus.github_relannis
			)
		return lines

	def _infer_html_visualization_formats_and_add_to_tx(self, corpus, corpus_dirname):
		try:
			vm = self._repo.file_contents("/".join([corpus_dirname, corpus.github_relannis, "resolver_vis_map.annis"]))
		except NotFoundError as e:
			raise ResolverVisMapIssue(
				corpus_dirname,
				self.corpus_repo_owner,
				self.corpus_repo_name,
				corpus.github_relannis
			) from e

		vis_lines = self._parse_resolver_vis_map(vm.decoded.decode('utf-8'), corpus, corpus_dirname)
		formats = []
		already_seen = []
		for _, _, _, _, type, vis_type, _, _, config_file in vis_lines:
			if type != "htmldoc":
				continue
			vis_type = vis_type.split(" ")[0]
			if not vis_type in self._known_visualization_formats or vis_type in already_seen:
				raise ResolverVisMapIssue(
					corpus_dirname,
					self.corpus_repo_owner,
					self.corpus_repo_name,
					corpus.github_relannis
				)
			self._vis_configs[vis_type] = re.findall(r'config:(?P<fname>.*)', config_file)[0]
			format = HtmlVisualizationFormat.objects.get(button_title=vis_type)
			formats.append(format)
			already_seen.append(vis_type)

		return formats

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
		corpus.github_tei, corpus.github_relannis, corpus.github_paula = self._infer_github_dirs(corpus, corpus_dirname)
		corpus.annis_corpus_name = self._infer_annis_corpus_name(corpus)
		corpus.slug = self._infer_slug(corpus)
		corpus.title = corpus.annis_corpus_name # User should edit this to something more appropriate

		# assignment to corpus.html_visualization_formats happen during the transaction
		self._current_transaction.add_vis_formats(self._infer_html_visualization_formats_and_add_to_tx(corpus, corpus_dirname))

		texts = self._get_texts(corpus, corpus_dirname)
		self._scrape_texts_and_add_to_tx(corpus, corpus_dirname, texts)

		# TODO: Revisit this once Carrie and Amir agree on a corpus URN determination scheme. For now, edit manually
		# corpus.urn_code = self._infer_urn_code(corpus_dirname)

		return self._current_transaction

	# - html_visualization_formats

	# text-level methods -----------------------------------------------------------------------------------------------

	def _scrape_texts_and_add_to_tx(self, corpus, corpus_dirname, texts):
		for contents in texts.values():
			self._current_text_contents = contents
			self._scrape_text_and_add_to_tx(corpus, corpus_dirname, contents)

	def _get_meta_dict(self, tt_lines):
		for line in tt_lines:
			if line.startswith('<meta'):
				return dict(re.findall(r'(?P<attr>\w+)="(?P<value>.*?)"', line))
		raise MetaNotFound(self.corpus_repo_owner, self.corpus_repo_name, self._current_text_contents.path)

	def _get_vis_config_file(self, corpus, corpus_dirname, config_file):
		path = corpus_dirname + "/" + corpus.annis_corpus_name + "/ExtData/" + config_file
		try:
			f = self._repo.file_contents(path)
		except NotFoundError as e:
			raise VisConfigIssue(path, self.corpus_repo_owner, self.corpus_repo_name) from e

	def _generate_visualizations_and_add_to_tx(self, corpus, corpus_dirname):
		for name, config_file in self._vis_configs.items():
			pass

	def _scrape_text_and_add_to_tx(self, corpus, corpus_dirname, contents):
		contents.refresh()
		tt_lines = contents.decoded.decode('utf-8').split("\n")

		meta = self._get_meta_dict(tt_lines)
		self._latest_meta_dict = meta

		text = Text()
		text.title = meta["title"]
		text.slug = slugify(meta["title"])
		text.corpus = self._current_corpus

		text_metas = [TextMeta(name=name, value=value) for name, value in meta.items()]

		self._generate_visualizations_and_add_to_tx(corpus, corpus_dirname)

		self._current_transaction.add_text((text, text_metas))








