from html import unescape
from collections import defaultdict
import re
from io import BytesIO
import zipfile
import base64
import requests

from django.db.models import Model
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import transaction
from django.db.models import ObjectDoesNotExist
from django.utils.text import slugify
from github3.exceptions import NotFoundError, ForbiddenError
from github3 import GitHub
from tqdm import tqdm

from texts.models import Corpus, Text, TextMeta, HtmlVisualization, HtmlVisualizationFormat
import texts.urn as urn
from .scraper_exceptions import *
from .htmlvis import generate_visualization
import os, io

script_dir = os.path.dirname(os.path.realpath(__file__)) + os.sep
name_mapping = io.open(script_dir + "name_mapping.tab", encoding="utf8").read().strip().split("\n")
corpus_urn_map = {}
corpus_title_map = {}
for line in name_mapping:
	if line.count("\t") == 2:
		corpus, corpus_title, corpus_urn = line.split("\t")
		corpus_urn_map[corpus] = corpus_urn
		corpus_title_map[corpus] = corpus_title

def get_git_blob(file_sha):
	headers = {}
	if getattr(settings, "GITHUB_TOKEN", "") != "":
		headers['Authorization'] = f'token {getattr(settings, "GITHUB_TOKEN")}'
	response = requests.get(
		f"{settings.GITHUB_API_BASE_URL}"
		f"/repos"
		f"/{settings.CORPUS_REPO_OWNER}"
		f"/{settings.CORPUS_REPO_NAME}"
		f"/git/blobs"
		f"/{file_sha}",
		headers=headers
	)
	content = response.json().get('content')
	content = base64.b64decode(content)
	content = content.decode('utf-8')
	return content


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

class TextContents:
    def __init__(self, path, contents):
        self.path = path
        self.contents = contents
        
class CorpusTransaction:
	"""Keeps track of every object that needs to be added to the SQL database for a given corpus,
	and atomically saves all of them."""

	def __init__(self, corpus_name, corpus):
		self.corpus_name = corpus_name
		self._corpus = corpus
		self._text_pairs = []
		self._vis_formats = []
		self._vises = []
		self._to_delete = []

	def add_objs_to_be_deleted(self, objs):
		self._to_delete = objs

	def add_text(self, text_pair):
		self._text_pairs.append(text_pair)

	def add_vis_formats(self, formats):
		self._vis_formats = formats

	def add_vis(self, text_and_vis):
		self._vises.append(text_and_vis)

	def sort_texts(self, text_next, text_prev, text_urn):
		"""
		Sorts texts based on next and previous metadata. Only actually changes their order if the next and previous
		attributes form an unbroken chain within the texts, otherwise does nothing.

		:param text_next: dict: text title -> text urn
		:param text_prev: dict: text title -> text urn
		:param text_urn: dict: text title -> text urn
		"""
		class Node:
			def __init__(self, title, orig_i):
				self.title = title
				self.orig_i = orig_i
				self.prev = None
				self.next = None

			def __str__(self):
				return f"<{self.title}, {self.orig_i}>"

			def __repr__(self):
				return self.__str__()

		urn_to_node = defaultdict(lambda: None)
		nodes = []
		for i, (text, _) in enumerate(self._text_pairs):
			node = Node(text.title, i)
			nodes.append(node)
			urn = text_urn[text.title] if text.title in text_urn else None
			urn_to_node[urn] = node

		def get_next_node(node):
			return urn_to_node[text_next[node.title]]

		def get_prev_node(node):
			return urn_to_node[text_prev[node.title]]

		for node in nodes:
			next_node = get_next_node(node)
			if next_node is not None: # and get_prev_node(next_node) == node:
				node.next = next_node
				next_node.prev = node

		start_node = nodes[0]
		while start_node.prev is not None:
			start_node = start_node.prev

		scan_node = start_node
		n_links = 0
		visited = [scan_node]
		while scan_node.next is not None and scan_node.next not in visited:
			n_links += 1
			scan_node = scan_node.next
			visited.append(scan_node.next)

		# refuse to cooperate if we don't have a full chain
		if n_links != len(nodes) - 1:
			print("Insufficient data to properly order corpus based on next/prev attrs.")
			return

		visited = []
		new_text_pairs = []
		node = start_node
		while node is not None and node not in visited:
			new_text_pairs.append(self._text_pairs[node.orig_i])
			visited.append(node)
			node = node.next

		self._text_pairs = new_text_pairs
		print("Successfully inferred proper ordering of corpus based on next/prev attrs.")

	@transaction.atomic
	def execute(self):
		if len(self._to_delete) > 0:
			print(f"Found an already existing upload of '{self.corpus_name}'. "
				f"It will be automatically deleted if this transaction succeeds.")
			for obj in self._to_delete:
				obj.delete()

		# Set visualization formats before initial save
		vis_format_instances = []
		for vis_format in self._vis_formats:
			try:
				vis_format_instance = HtmlVisualizationFormat.objects.get(slug=vis_format.slug)
				if vis_format_instance:
					vis_format_instances.append(vis_format_instance)
			except HtmlVisualizationFormat.DoesNotExist:
				print(f"Warning: Visualization format '{vis_format.slug}' not found")
				continue

		if vis_format_instances:
			print(f"Our instances: {vis_format_instances}")
			self._corpus.set_visualization_formats(vis_format_instances)
		
		self._corpus.save()

		# Rest of the method remains unchanged
		for text, text_metas in self._text_pairs:
			for text_meta in text_metas:
				text_meta.save()

			corpus = text.corpus
			text.corpus = None
			text.save()

			text.corpus = corpus
			text.save()

			for text_meta in text_metas:
				text.text_meta.add(text_meta)
			text.save()

		for text, vis in self._vises:
			vis.save()
			text.html_visualizations.add(vis)
			text.save()

		return {"texts": len(self._text_pairs),
				"text_metas": sum(map(lambda x: len(x[1]), self._text_pairs)),
				"vises": len(self._vises)}


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
                        token=getattr(settings, "GITHUB_TOKEN", ""),
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
		self._known_visualization_formats = HtmlVisualizationFormat.objects.values_list('button_title', flat=True)

		# a map from the visualization subtype (identical to a val of HtmlVisualizationFormat's button_title field)
		# to the file in ExtData that contains information about it
		self._vis_configs = {}

		# holds the actual values of dipl.config, dipl.css, etc.
		self._vis_config_contents = {}
		self._vis_css_contents = {}

		# Text -> meta.prev, meta.next, meta.document_cts_urn
		self._text_next = defaultdict(lambda: None)
		self._text_prev = defaultdict(lambda: None)
		self._text_urn = defaultdict(lambda: None)

	def _get_zipfile_for_blob(self, sha):
		blob = self._repo.blob(sha)
		blob = base64.b64decode(blob.content)

		zip_data = BytesIO()
		zip_data.write(blob)
		return zipfile.ZipFile(zip_data)

	# misc methods for zipped files
	def _get_blob_contents(self, sha, filename):
		zip_file = self._get_zipfile_for_blob(sha)
		return zip_file.open(filename).read().decode('utf-8')

	def _get_all_zipped_files(self, sha):
		zip_file = self._get_zipfile_for_blob(sha)

		files_and_contents = []
		for filename in zip_file.namelist():
			zfile = zip_file.open(filename)
			files_and_contents.append((filename, zfile.read().decode('utf-8')))
		return files_and_contents

	# corpus-level methods ---------------------------------------------------------------------------------------------

	def parse_corpora(self, corpus_dirnames):
		corpora = []
		for corpus_dirname in corpus_dirnames:
			# reset internal state
			self.__init__()
			corpora.append(self.parse_corpus(corpus_dirname))
		return corpora

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
				if contents.type == 'dir' or name.endswith('.zip')]
		github_tei = self._infer_dir(corpus, dirs, "_TEI", "_TEI.zip")
		github_relannis = self._infer_dir(corpus, dirs, "_ANNIS", "_RELANNIS", "_RELANNIS.zip", "_ANNIS.zip")
		github_paula = self._infer_dir(corpus, dirs, "_PAULA", "_PAULA.zip")
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
			return slugify(corpus.annis_corpus_name)

	def _get_texts(self, corpus, corpus_dirname):
		try:
			if corpus.github_paula.endswith(".zip"):
				vm = dict(self._repo.directory_contents(corpus_dirname))
				dir_contents = self._get_all_zipped_files(
					vm[corpus.annis_corpus_name + "_TT.zip"].sha)
				texts = [(name, contents) for name, contents in dir_contents]
			else:
				tt_dir = corpus_dirname + "/" + corpus.annis_corpus_name + "_TT"
				dir_contents = self._repo.directory_contents(tt_dir)

				#texts = [(name, contents.refresh().decoded.decode('utf-8')) for name, contents in dir_contents]
				# had to rewrite this because github3.py relies on a GitHub API that refuses to serve blobs >1MB in size
				texts = []
				for name, contents in dir_contents:
					try:
						contents = contents.refresh().decoded.decode('utf-8')
					except ForbiddenError:
						contents = get_git_blob(contents.sha)
					texts.append((name, contents))
		except NotFoundError as e:
			raise TTDirMissing(corpus_dirname, self.corpus_repo_owner, self.corpus_repo_name, tt_dir) from e

		if len(texts) == 0:
			raise NoTexts(corpus_dirname, self.corpus_repo_owner, self.corpus_repo_name, tt_dir)

		return dict(texts)

	def _infer_urn_code(self, corpus_dirname):
		meta = self._latest_meta_dict
		if meta is None or "document_cts_urn" not in meta:
			#raise InferenceError(corpus_dirname, self.corpus_repo_owner, self.corpus_repo_name, "urn_code")
			return ""

		doc_urn = meta["document_cts_urn"]
		# TODO: for most corpora right now, it seems like the "corpus urn" actually corresponds to a Text
		# rather than a Corpus. Use textgroup instead, revisit when the CS team makes a decision on standardizing URNs.
		corpus_urn = urn.textgroup_urn(doc_urn)
		# corpus_urn = urn.corpus_urn(doc_urn)
		#if corpus_urn == "":
		#	raise InferenceError(corpus_dirname, self.corpus_repo_owner, self.corpus_repo_name, "urn_code")

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
			if corpus.github_relannis.endswith("zip"):
				vm = dict(self._repo.directory_contents(corpus_dirname))
				vm = self._get_blob_contents(vm[corpus.github_relannis].sha, "resolver_vis_map.annis")
			else:
				vm = self._repo.file_contents("/".join([corpus_dirname, corpus.github_relannis, "resolver_vis_map.annis"]))
				vm = vm.decoded.decode('utf-8')
		except (NotFoundError, IndexError) as e:
			raise ResolverVisMapIssue(
				corpus_dirname,
				self.corpus_repo_owner,
				self.corpus_repo_name,
				corpus.github_relannis
			) from e

		vis_lines = self._parse_resolver_vis_map(vm, corpus, corpus_dirname)
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

	@transaction.atomic
	def parse_corpus(self, corpus_dirname):
		if corpus_dirname not in self._corpora:
			raise CorpusNotFound(corpus_dirname, self.corpus_repo_owner, self.corpus_repo_name)

		corpus = Corpus()
		self._current_corpus = corpus
		# All objects we make will go into this list
		self._current_transaction = CorpusTransaction(corpus_dirname, corpus)

		# Delete any already-existing corpus object
		github_url = f"https://github.com/{self.corpus_repo_owner}/{self.corpus_repo_name}/tree/master/{corpus_dirname}"
		try:
			existing_corpus = Corpus.objects.get(github=github_url)
			# delete text_meta manually because they're not linked with foreign keys--all others will be handled by
			# the cascading sql delete
			to_delete = []
			for text in Text.objects.all().filter(corpus=existing_corpus):
				for text_meta in text.text_meta.all():
					to_delete.append(text_meta)
			to_delete.append(existing_corpus)
			self._current_transaction.add_objs_to_be_deleted(to_delete)
		except ObjectDoesNotExist:
			pass

		corpus.slug = corpus_dirname # provisionally, until we find the real one, so we can use this in errors
		corpus.github = f"https://github.com/{self.corpus_repo_owner}/{self.corpus_repo_name}/tree/master/{corpus_dirname}"
		corpus.github_tei, corpus.github_relannis, corpus.github_paula = self._infer_github_dirs(corpus, corpus_dirname)
		corpus.annis_corpus_name = self._infer_annis_corpus_name(corpus)
		corpus.slug = self._infer_slug(corpus)
		if corpus.annis_corpus_name in corpus_title_map:
			corpus.title = corpus_title_map[corpus.annis_corpus_name]
		else:
			corpus.title = corpus.annis_corpus_name # User should edit this to something more appropriate

		# assignment to corpus.html_visualization_formats happen during the transaction
		self._current_transaction.add_vis_formats(self._infer_html_visualization_formats_and_add_to_tx(corpus, corpus_dirname))

		texts = self._get_texts(corpus, corpus_dirname)
		self._scrape_texts_and_add_to_tx(corpus, corpus_dirname, texts)
		self._current_transaction.sort_texts(self._text_next, self._text_prev, self._text_urn)

		if corpus.annis_corpus_name in corpus_urn_map:
			corpus.urn_code = corpus_urn_map[corpus.annis_corpus_name]
		else:
			corpus.urn_code = self._infer_urn_code(corpus_dirname)

		return self._current_transaction

	# text-level methods -----------------------------------------------------------------------------------------------
	def _load_config_files(self, corpus, corpus_dirname):
		# load config and css for visualizations
		files = dict(self._repo.directory_contents(corpus_dirname))
		if corpus.github_relannis.endswith('zip'):
			zip_file = self._get_zipfile_for_blob(files[corpus.github_relannis].sha)
		else:
			zip_file = None
		for name, config_file in self._vis_configs.items():
			self._vis_config_contents[name] = self._get_vis_config_file(corpus, corpus_dirname, config_file, zip_file)
			self._vis_css_contents[name] = self._get_vis_css_file(corpus, corpus_dirname, config_file, zip_file)

	def _scrape_texts_and_add_to_tx(self, corpus, corpus_dirname, texts):
		print(f"Preparing transaction for '{corpus_dirname}'...")
		self._load_config_files(corpus, corpus_dirname)
		for name, contents in tqdm(texts.items(), ncols=80):
			self._current_text_contents = contents
			self._scrape_text_and_add_to_tx(corpus, corpus_dirname, contents)

	def _get_meta_dict(self, tt_lines):
		for line in tt_lines:
			if line.startswith('<meta'):
				return dict(re.findall(r'(?P<attr>[\w._-]+)="(?P<value>.*?)"', line))
		raise MetaNotFound(self.corpus_repo_owner, self.corpus_repo_name, self._current_text_contents)

	def _get_vis_css_file(self, corpus, corpus_dirname, config_file, zip_file):
		try:
			if zip_file:
				path = "ExtData/" + config_file + ".css"
				return zip_file.open(path).read().decode('utf-8')
			else:
				path = corpus_dirname + "/" + corpus.github_relannis + "/ExtData/" + config_file + ".css"
				f = self._repo.file_contents(path)
				return f.decoded.decode('utf-8')
		except NotFoundError:
			return ""

	def _get_vis_config_file(self, corpus, corpus_dirname, config_file, zip_file):
		try:
			if zip_file:
				path = "ExtData/" + config_file + ".config"
				return zip_file.open(path).read().decode('utf-8')
			else:
				path = corpus_dirname + "/" + corpus.github_relannis + "/ExtData/" + config_file + ".config"
				f = self._repo.file_contents(path)
				return f.decoded.decode('utf-8')
		except NotFoundError as e:
			raise VisConfigIssue(path, self.corpus_repo_owner, self.corpus_repo_name) from e

	def _generate_visualizations_and_add_to_tx(self, text, contents):
		for name, config_file in self._vis_configs.items():
			config_text = self._vis_config_contents[name]
			config_css = self._vis_css_contents[name]
			rendered_html = generate_visualization(config_text, contents, css_text=config_css)
			vis = HtmlVisualization()
			format = HtmlVisualizationFormat.objects.get(button_title=name)
			vis.visualization_format_slug = format.slug  # Use the new field
			vis.html = rendered_html
			self._current_transaction.add_vis((text, vis))

	def _scrape_text_and_add_to_tx(self, corpus, corpus_dirname, contents):
		tt_lines = contents.split("\n")

		meta = self._get_meta_dict(tt_lines)
		self._latest_meta_dict = meta

		text = Text()
		text.title = meta["title"]
		text.slug = slugify(meta["title"] if "title" in meta else meta["name"])
		text.corpus = self._current_corpus
		self._text_next[text.title] = meta["next"] if "next" in meta else None
		self._text_prev[text.title] = meta["previous"] if "previous" in meta else None
		self._text_urn[text.title] = meta["document_cts_urn"] if "document_cts_urn" in meta else None

		text_metas = [TextMeta(name=name, value=unescape(value)) for name, value in meta.items()]

		self._generate_visualizations_and_add_to_tx(text, contents)

		self._current_transaction.add_text((text, text_metas))

class LocalCorpusScraper:

    def __init__(self):
        
        self.local_repo_path = get_setting_and_error_if_none(
            "LOCAL_REPO_PATH",
            "A local repository path must be specified."
        )
        self._corpora = [d for d in os.listdir(self.local_repo_path) if os.path.isdir(os.path.join(self.local_repo_path, d))]

        self._current_corpus = None
        self._current_transaction = None
        self._current_text_contents = None
        self._latest_meta_dict = None

        self._known_visualization_formats = HtmlVisualizationFormat.objects.values_list('button_title', flat=True)
        self._vis_configs = {}
        self._vis_config_contents = {}
        self._vis_css_contents = {}

        self._text_next = defaultdict(lambda: None)
        self._text_prev = defaultdict(lambda: None)
        self._text_urn = defaultdict(lambda: None)

    def _get_zipfile_for_blob(self, path):
        with open(path, 'rb') as f:
            zip_data = BytesIO(f.read())
        return zipfile.ZipFile(zip_data)

    def _get_blob_contents(self, path, filename):
        zip_file = self._get_zipfile_for_blob(path)
        return zip_file.open(filename).read().decode('utf-8')

    def _get_all_files_in_zip(self, zip_path):
        files_and_contents = []
        with zipfile.ZipFile(zip_path, 'r') as zfile:
            for filename in zfile.namelist():
                with zfile.open(filename) as file:
                    content = file.read()
                    if content.startswith(b'PK\x03\x04'):
                        # If the content is a zip file, recurse
                        nested_files = self._get_all_files_in_zip(BytesIO(content))
                        files_and_contents.extend(nested_files)
                    else:
                        try:
                            content = content.decode('utf-8')
                        except UnicodeDecodeError:
                            # Handle binary content or other encodings if necessary
                            pass
                        files_and_contents.append((filename, content))
        return files_and_contents

    def parse_corpora(self, corpus_dirnames):
        corpora = []
        for corpus_dirname in corpus_dirnames:
            self.__init__()
            corpora.append(self.parse_corpus(corpus_dirname))
        return corpora

    def _infer_dir(self, corpus, dirs, *exts):
        target_dirs = []
        for ext in exts:
            if len(target_dirs) == 0:
                target_dirs = [x for x in dirs if x.lower().endswith(ext.lower())]
        if len(target_dirs) > 1:
            raise LocalAmbiguousCorpus(corpus.slug, self.local_repo_path)
        return target_dirs[0] if len(target_dirs) == 1 else ''

    def _infer_local_dirs(self, corpus, corpus_dirname):
        corpus_path = os.path.join(self.local_repo_path, corpus_dirname)
        dirs = [name for name in os.listdir(corpus_path) if os.path.isdir(os.path.join(corpus_path, name)) or name.endswith('.zip')]
        local_tei = self._infer_dir(corpus, dirs, "_TEI", "_TEI.zip")
        local_relannis = self._infer_dir(corpus, dirs, "_ANNIS", "_RELANNIS", "_RELANNIS.zip", "_ANNIS.zip")
        local_paula = self._infer_dir(corpus, dirs, "_PAULA", "_PAULA.zip")
        if not any(str(x) and x != '' for x in [local_tei, local_paula, local_relannis]):
            raise LocalEmptyCorpus(corpus_dirname, self.local_repo_path)
        return local_tei, local_relannis, local_paula

    def _infer_annis_corpus_name(self, corpus):
        if corpus.github_tei != '':
            return corpus.github_tei[:corpus.github_tei.rfind("_")]
        elif corpus.github_relannis != '':
            return corpus.github_relannis[:corpus.github_relannis.rfind("_")]
        elif corpus.github_paula != '':
            return corpus.github_paula[:corpus.github_paula.rfind("_")]
        else:
            raise LocalInferenceError(corpus.slug, self.local_repo_path, "annis_corpus_name")

    def _infer_slug(self, corpus):
        if corpus.annis_corpus_name in KNOWN_SLUGS:
            return KNOWN_SLUGS[corpus.annis_corpus_name]
        else:
            return slugify(corpus.annis_corpus_name)

    def _get_texts(self, corpus, corpus_dirname):
        corpus_path = os.path.join(self.local_repo_path, corpus_dirname)
        texts = []

        try:
            if corpus.github_paula.endswith("zip"):
                dir_contents = self._get_all_files_in_zip(os.path.join(corpus_path, corpus.github_paula))
                texts = [(name, contents) for name, contents in dir_contents]
            else:
                tt_dir = os.path.join(corpus_path, corpus.annis_corpus_name + "_TT")
                dir_contents = os.listdir(tt_dir)
                texts = [(name, open(os.path.join(tt_dir, name)).read()) for name in dir_contents]
        except FileNotFoundError as e:
            tt_dir = os.path.join(corpus_path, corpus.annis_corpus_name + "_TT")
            raise LocalTTDirMissing(corpus_dirname, self.local_repo_path, tt_dir) from e

        if len(texts) == 0:
            raise LocalNoTexts(corpus_dirname, self.local_repo_path, tt_dir)

        return dict(texts)

    def _infer_urn_code(self, corpus_dirname):
        meta = self._latest_meta_dict
        if meta is None or "document_cts_urn" not in meta:
            return ""

        doc_urn = meta["document_cts_urn"]
        corpus_urn = urn.textgroup_urn(doc_urn)
        return corpus_urn

    def _parse_resolver_vis_map(self, text, corpus, corpus_dirname):
        lines = text.strip().split("\n")
        lines = [line.split("\t") for line in lines]
        if not all(len(line) == 9 for line in lines):
            raise LocalResolverVisMapIssue(corpus_dirname, self.local_repo_path, corpus.github_relannis)
        return lines

    def _infer_html_visualization_formats_and_add_to_tx(self, corpus, corpus_dirname):
        try:
            if corpus.github_relannis.endswith("zip"):
                vm = self._get_blob_contents(os.path.join(self.local_repo_path, corpus_dirname, corpus.github_relannis), "resolver_vis_map.annis")
            else:
                vm_path = os.path.join(self.local_repo_path, corpus_dirname, corpus.github_relannis, "resolver_vis_map.annis")
                with open(vm_path, 'r') as f:
                    vm = f.read()
        except (FileNotFoundError, IndexError) as e:
            raise LocalResolverVisMapIssue(corpus_dirname, self.local_repo_path, corpus.github_relannis) from e

        vis_lines = self._parse_resolver_vis_map(vm, corpus, corpus_dirname)
        formats = []
        already_seen = []
        for _, _, _, _, type, vis_type, _, _, config_file in vis_lines:
            if type != "htmldoc":
                continue
            vis_type = vis_type.split(" ")[0]
            if not vis_type in self._known_visualization_formats or vis_type in already_seen:
                raise LocalResolverVisMapIssue(corpus_dirname, self.local_repo_path, corpus.github_relannis)
            self._vis_configs[vis_type] = re.findall(r'config:(?P<fname>.*)', config_file)[0]
            format = HtmlVisualizationFormat.objects.get(button_title=vis_type)
            formats.append(format)
            already_seen.append(vis_type)

        return formats

    @transaction.atomic
    def parse_corpus(self, corpus_dirname):
        if corpus_dirname not in self._corpora:
            raise LocalCorpusNotFound(corpus_dirname, self.local_repo_path)

        corpus = Corpus()
        self._current_corpus = corpus
        self._current_transaction = CorpusTransaction(corpus_dirname, corpus)

        github_url = f"file://{os.path.join(self.local_repo_path, corpus_dirname)}"
        try:
            existing_corpus = Corpus.objects.get(github=github_url)
            to_delete = []
            for text in Text.objects.all().filter(corpus=existing_corpus):
                for text_meta in text.text_meta.all():
                    to_delete.append(text_meta)
            to_delete.append(existing_corpus)
            self._current_transaction.add_objs_to_be_deleted(to_delete)
        except ObjectDoesNotExist:
            pass

        corpus.slug = corpus_dirname
        corpus.github = github_url
        corpus.github_tei, corpus.github_relannis, corpus.github_paula = self._infer_local_dirs(corpus, corpus_dirname)
        corpus.annis_corpus_name = self._infer_annis_corpus_name(corpus)
        corpus.slug = self._infer_slug(corpus)
        if corpus.annis_corpus_name in corpus_title_map:
            corpus.title = corpus_title_map[corpus.annis_corpus_name]
        else:
            corpus.title = corpus.annis_corpus_name

        self._current_transaction.add_vis_formats(self._infer_html_visualization_formats_and_add_to_tx(corpus, corpus_dirname))

        texts = self._get_texts(corpus, corpus_dirname)
        self._scrape_texts_and_add_to_tx(corpus, corpus_dirname, texts)
        self._current_transaction.sort_texts(self._text_next, self._text_prev, self._text_urn)

        if corpus.annis_corpus_name in corpus_urn_map:
            corpus.urn_code = corpus_urn_map[corpus.annis_corpus_name]
        else:
            corpus.urn_code = self._infer_urn_code(corpus_dirname)

        return self._current_transaction

    def _load_config_files(self, corpus, corpus_dirname):
        corpus_path = os.path.join(self.local_repo_path, corpus_dirname)
        files = os.listdir(corpus_path)
        if corpus.github_relannis.endswith('zip'):
            zip_file = self._get_zipfile_for_blob(os.path.join(corpus_path, corpus.github_relannis))
        else:
            zip_file = None
        for name, config_file in self._vis_configs.items():
            self._vis_config_contents[name] = self._get_vis_config_file(corpus, corpus_dirname, config_file, zip_file)
            self._vis_css_contents[name] = self._get_vis_css_file(corpus, corpus_dirname, config_file, zip_file)

    def _scrape_texts_and_add_to_tx(self, corpus, corpus_dirname, texts):
        print(f"Preparing transaction for '{corpus_dirname}'...")
        self._load_config_files(corpus, corpus_dirname)
        for name, contents in tqdm(texts.items(), ncols=80):
            if contents:
                self._current_text_contents = contents
                self._scrape_text_and_add_to_tx(corpus, corpus_dirname, contents)

    def _get_meta_dict(self, tt_lines):
        for line in tt_lines:
            if line.startswith('<meta'):
                return dict(re.findall(r'(?P<attr>[\w._-]+)="(?P<value>.*?)"', line))
        raise LocalMetaNotFound(self.local_repo_path, self._current_text_contents.path)

    def _get_vis_css_file(self, corpus, corpus_dirname, config_file, zip_file):
        try:
            if zip_file:
                path = "ExtData/" + config_file + ".css"
                return zip_file.open(path).read().decode('utf-8')
            else:
                path = os.path.join(self.local_repo_path, corpus_dirname, corpus.github_relannis, "ExtData", config_file + ".css")
                with open(path, 'r') as f:
                    return f.read()
        except FileNotFoundError:
            return ""

    def _get_vis_config_file(self, corpus, corpus_dirname, config_file, zip_file):
        try:
            if zip_file:
                path = "ExtData/" + config_file + ".config"
                return zip_file.open(path).read().decode('utf-8')
            else:
                path = os.path.join(self.local_repo_path, corpus_dirname, corpus.github_relannis, "ExtData", config_file + ".config")
                with open(path, 'r') as f:
                    return f.read()
        except FileNotFoundError as e:
            raise LocalVisConfigIssue(path, self.local_repo_path) from e

    def _generate_visualizations_and_add_to_tx(self, text, contents):
        for name, config_file in self._vis_configs.items():
            config_text = self._vis_config_contents[name]
            config_css = self._vis_css_contents[name]
            rendered_html = generate_visualization(config_text, contents, css_text=config_css)
            vis = HtmlVisualization()
            format = HtmlVisualizationFormat.objects.get(button_title=name)
            vis.visualization_format_slug = format.slug
            vis.html = rendered_html
            self._current_transaction.add_vis((text, vis))

    def _scrape_text_and_add_to_tx(self, corpus, corpus_dirname, contents):
        tt_lines = contents.split("\n")
        meta = self._get_meta_dict(tt_lines)
        self._latest_meta_dict = meta

        text = Text()
        text.title = meta["title"]
        text.slug = slugify(meta["title"] if "title" in meta else meta["name"])
        text.corpus = self._current_corpus
        self._text_next[text.title] = meta["next"] if "next" in meta else None
        self._text_prev[text.title] = meta["previous"] if "previous" in meta else None
        self._text_urn[text.title] = meta["document_cts_urn"] if "document_cts_urn" in meta else None

        text_metas = [TextMeta(name=name, value=unescape(value)) for name, value in meta.items()]

        self._generate_visualizations_and_add_to_tx(text, contents)

        self._current_transaction.add_text((text, text_metas))