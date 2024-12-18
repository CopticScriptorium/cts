from html import unescape
from collections import defaultdict
import re
from io import BytesIO
import csv
from io import StringIO
import zipfile
from django.core.exceptions import ImproperlyConfigured
from django.conf import settings
from django.db import transaction
from django.utils.text import slugify

from tqdm import tqdm

from coptic.settings.base import HTML_CONFIGS, KNOWN_SLUGS
from gh_ingest.corpus_transaction import CorpusTransaction
from texts.models import (
    Corpus,
    Text,
    TextMeta,
    HtmlVisualization,
    HtmlVisualizationFormat,
)
import texts.urn as urn
from .scraper_exceptions import *
from .htmlvis import generate_visualization
import os
import subprocess
import csv

# Determine the script directory
script_dir = os.path.dirname(os.path.realpath(__file__)) + os.sep

# Initialize mappings
corpus_urn_map = {}
corpus_title_map = {}

# Open the file and use csv.reader to parse it
with open(script_dir + "name_mapping.tab", encoding="utf8") as file:
    reader = csv.reader(file, delimiter="\t")
    for row in reader:
            corpus, corpus_title, corpus_urn = row
            corpus_urn_map[corpus] = corpus_urn
            corpus_title_map[corpus] = corpus_title

def get_setting_and_error_if_none(var_name, error_message):
    var = getattr(settings, var_name, None)
    if var is None:
        raise ImproperlyConfigured(error_message)
    return var

class CorpusScraper:
    def __init__(self):
        """
        Initializes the CorpusScraper instance.

        This constructor sets up the initial configuration for the CorpusScraper,
        ensures the local repository is available, and initializes various attributes
        related to the corpus and visualization formats.

        Attributes:
            corpus_repo_name (str): The name of the corpus repository.
            corpus_repo_owner (str): The owner of the corpus repository.
            repo_path (str): The local path to the repository.
            _corpora (list): A list of directories in the local repository path that represent corpora.
            _current_corpus (str): The currently selected corpus.
            _current_transaction (str): The current transaction.
            _current_text_contents (str): The contents of the current text.
            _latest_meta_dict (dict): The latest metadata dictionary.
            _text_next (defaultdict): A defaultdict for the next text.
            _text_prev (defaultdict): A defaultdict for the previous text.
            _text_urn (defaultdict): A defaultdict for the text URN.
        """
        # We use these urls to identify the corpus- which 
        # we should probably change. But later.
        # FIXME: Change this to a more general way of identifying a corpus
        self.corpus_repo_name = None
        self.corpus_repo_owner = None
        self.repo_path = None

        self._init_config()
        self.ensure_repo()
        # get all the directories where we have our corpora, ignoring
        # hidden directories and special ones.
        self._corpora = [
            d
            for d in os.listdir(self.repo_path)
            if os.path.isdir(os.path.join(self.repo_path, d)) and not d.startswith('.')
        ]

        self._current_corpus = None
        self._current_transaction = None
        self._current_text_contents = None
        self._latest_meta_dict = None
        self._vis_configs = {}
        self._vis_config_contents = {}

        self._text_next = defaultdict(lambda: None)
        self._text_prev = defaultdict(lambda: None)
        self._text_urn = defaultdict(lambda: None)

    def ensure_repo(self):
        if not os.path.exists(self.repo_path):
            self.clone_repo()
        else:
            self.pull_repo()

    def clone_repo(self):
        try:
            repo_url = f"https://github.com/{self.corpus_repo_owner}/{self.corpus_repo_name}.git"
            subprocess.run(["git", "clone", repo_url, self.repo_path], check=True)
            print(f"Cloned repository from {repo_url} to {self.repo_path}")
        except:
            print(f"Could not clone repository from probably offline, but do please check the error")

    def pull_repo(self):
        try:
            subprocess.run(["git", "-C", self.repo_path, "pull"], check=True)
            print(f"Pulled latest changes in repository at {self.repo_path}")
        except:
            print(f"Could not pull repository from  upstream probably offline")

    def _get_tree_id(self, path):
        try:
            result = subprocess.run(
                ["git", "-C", self.repo_path, "rev-parse", "HEAD:" + path],
                capture_output=True,
                text=True,
                check=True,
            )
        except:
            raise TTDirMissing("", self.repo_path, path)
        return result.stdout.strip()
    
    def _init_config(self):
        try:
            if not self.corpus_repo_owner:
                self.corpus_repo_owner = get_setting_and_error_if_none(
                    "CORPUS_REPO_OWNER",
                    "A corpus repository owner must be specified, e.g. 'CopticScriptorium' if the "
                    "URL is https://github.com/CopticScriptorium/corpora",
                )
        except:
            print("CORPUS_REPO_OWNER not found in settings. Using default value CopticScriptorium.")
            self.corpus_repo_owner = "CopticScriptorium"
        try: 
            if not self.corpus_repo_name:
                self.corpus_repo_name = get_setting_and_error_if_none(
                    "CORPUS_REPO_NAME",
                    "A corpus repository name must be specified, e.g. 'corpora' if the "
                    "URL is https://github.com/CopticScriptorium/corpora",
                )
        except:
            print("CORPUS_REPO_NAME not found in settings. Using default value corpora.")
            self.corpus_repo_name = "corpora"
        try:
            if not self.repo_path:
                self.repo_path = get_setting_and_error_if_none(
                    "LOCAL_REPO_PATH", "A local repository path must be specified."
                )
        except:
            print("LOCAL_REPO_PATH not found in settings. Using default value ../../corpora.")
            self.repo_path = "../../corpora"

    def _get_zip_for_file(self, path):
        with open(path, "rb") as f:
            zip_data = BytesIO(f.read())
        return zipfile.ZipFile(zip_data)

    def _get_zip_file_contents(self, path, filename):
        zip_file = self._get_zip_for_file(path)
        return zip_file.open(filename).read().decode("utf-8")

    def _get_all_files_in_zip(self, zip_path):
        files_and_contents = []
        with zipfile.ZipFile(zip_path, "r") as zfile:
            for filename in zfile.namelist():
                with zfile.open(filename) as file:
                    content = file.read()
                    if content.startswith(b"PK\x03\x04"):
                        # If the content is a zip file, recurse
                        # This is using the magic number for zip files
                        nested_files = self._get_all_files_in_zip(BytesIO(content))
                        files_and_contents.extend(nested_files)
                    else:
                        try:
                            content = content.decode("utf-8")
                        except UnicodeDecodeError:
                            # Handle binary content or other encodings if necessary
                            # FIXME: I don't think we should pass here. We should raise an exception.
                            pass
                        files_and_contents.append((filename, content))
        return files_and_contents

    def parse_corpora(self, corpus_dirnames):
        corpora = []
        for corpus_dirname in corpus_dirnames:
            corpora.append(self.parse_corpus(corpus_dirname))
        return corpora

    def _infer_dirs(self, corpus, corpus_dirname):
        corpus_path = os.path.join(self.repo_path, corpus_dirname)
        dirs = [name for name in os.listdir(corpus_path) if os.path.isdir(os.path.join(corpus_path, name)) or name.endswith(".zip")]

        def find_dir(suffix):
            matched_dirs = [d for d in dirs if suffix in d]
            if len(matched_dirs) > 1:
                raise AmbiguousCorpus(corpus.slug, self.repo_path)
            return matched_dirs[0] if matched_dirs else ""

        tei = find_dir("_TEI")
        relannis = find_dir("ANNIS")
        paula = find_dir("_PAULA")

        if not (tei or relannis or paula):
            raise EmptyCorpus(corpus_dirname, self.repo_path)

        return tei, relannis, paula

    def _get_texts(self, corpus, corpus_dirname):
        corpus_path = os.path.join(self.repo_path, corpus_dirname)
        text_tree_id = self._get_tree_id(corpus_dirname)
        
        texts = []

        try:
            if corpus.github_relannis.endswith("zip"):
                dir_contents = self._get_all_files_in_zip(
                    os.path.join(corpus_path, corpus.annis_corpus_name + "_TT.zip")
                )
                texts = [(name, contents) for name, contents in dir_contents]
            else:
                tt_dir = os.path.join(corpus_path, corpus.annis_corpus_name + "_TT")
                dir_contents = os.listdir(tt_dir)
                texts = [
                    (name, open(os.path.join(tt_dir, name)).read())
                    for name in dir_contents
                ]
        except FileNotFoundError as e:
            tt_dir = os.path.join(corpus_path, corpus.annis_corpus_name + "_TT")
            raise TTDirMissing(corpus_dirname, self.repo_path, tt_dir) from e

        if len(texts) == 0:
            raise NoTexts(corpus_dirname, self.repo_path, tt_dir)

        return dict(texts), text_tree_id

    def _infer_html_visualization_formats_and_add_to_tx(self, corpus, corpus_dirname):
        vis_map_content = StringIO(self.get_resolver_vis_map_content(corpus, corpus_dirname))
        reader = csv.reader(vis_map_content, delimiter="\t", lineterminator="\n")
        formats=[] # this is a list because we want them unique
        for row in reader:
            if row[4]=="htmldoc": # if the fourth column is htmldoc
                vis_type= row[8].split("config:")[1] # extract the format type
                format = HtmlVisualizationFormat.objects.get(slug=vis_type)
                if format and format not in formats:
                    formats.append(format)
        return formats

    def get_resolver_vis_map_content(self, corpus, corpus_dirname):
        file_name = "resolver_vis_map.annis"
        vm_path = os.path.join(
                    self.repo_path,
                    corpus_dirname,
                    corpus.github_relannis,
                )
        try:
            if corpus.github_relannis.endswith("zip"):
                vm = self._get_zip_file_contents(vm_path, file_name)
            else:
                with open(os.path.join(vm_path, file_name)) as f:
                    vm = f.read()
        except (FileNotFoundError, IndexError) as e:
            raise ResolverVisMapIssue(
                corpus_dirname, self.repo_path, corpus.github_relannis
            ) from e
            
        return vm

    @transaction.atomic
    def parse_corpus(self, corpus_dirname):
        if corpus_dirname not in self._corpora:
            raise CorpusNotFound(corpus_dirname, self.repo_path)

        corpus = Corpus()
        self._current_corpus = corpus
        self._current_transaction = CorpusTransaction(corpus_dirname, corpus)

        github_url = f"https://github.com/{self.corpus_repo_owner}/{self.corpus_repo_name}/tree/master/{corpus_dirname}"
        print(f"Processing '{github_url}' from '{self.repo_path}'...")
        existing_corpus = Corpus.objects.filter(github=github_url).first()

        if existing_corpus:
            to_delete = []
            # FIXME: we should probably give an option not
            # to reimport existing corpora if the tree_id matches
            for text in Text.objects.all().filter(corpus=existing_corpus):
                for text_meta in text.text_meta.all():
                    to_delete.append(text_meta)
            to_delete.append(existing_corpus)
            self._current_transaction.add_objs_to_be_deleted(to_delete)

        corpus.slug = corpus_dirname
        corpus.github = github_url
        corpus.github_tei, corpus.github_relannis, corpus.github_paula = (
            self._infer_dirs(corpus, corpus_dirname)
        )
        corpus.annis_corpus_name = corpus.github_relannis[: corpus.github_relannis.rfind("_")]
        if corpus.annis_corpus_name in KNOWN_SLUGS:
            corpus.slug = KNOWN_SLUGS[corpus.annis_corpus_name]
        else:
            corpus.slug = slugify(corpus.annis_corpus_name)
            
        if corpus.annis_corpus_name in corpus_title_map:
            corpus.title = corpus_title_map[corpus.annis_corpus_name]
            print(f"Found title for '{corpus.annis_corpus_name}': '{corpus.title}'")
        else:
            corpus.title = corpus.annis_corpus_name
            print(f"Title not found for '{corpus.annis_corpus_name}'. Using '{corpus.title}'")

        self._current_transaction.add_vis_formats(
            self._infer_html_visualization_formats_and_add_to_tx(corpus, corpus_dirname)
        )

        texts, tree_id = self._get_texts(corpus, corpus_dirname)
        self._scrape_texts_and_add_to_tx(corpus, corpus_dirname, texts, tree_id)
        self._current_transaction.sort_texts(
            self._text_next, self._text_prev, self._text_urn
        )

        # first prefer the explicit map
        if corpus.annis_corpus_name in corpus_urn_map:
            corpus.urn_code = corpus_urn_map[corpus.annis_corpus_name]
        # then if we have no meta or we don't have document_cts_urn set the urn code to empty
        elif self._latest_meta_dict is None or "document_cts_urn" not in self._latest_meta_dict:
            corpus.urn_code = ""
        # Finally set the urn code to whatever is in _latest_meta_dict
        # FIXME: figure out _latest_meta_dict
        else:
            corpus.urn_code = urn.textgroup_urn(self._latest_meta_dict["document_cts_urn"])
        return self._current_transaction

    def _scrape_texts_and_add_to_tx(self, corpus, corpus_dirname, texts, tree_id):
        print(f"Preparing transaction for '{corpus_dirname}'...")
        for filename, contents in tqdm(texts.items(), ncols=80):
            if contents:
                self._current_text_contents = contents
                self._scrape_text_and_add_to_tx(corpus, corpus_dirname, contents, tree_id, filename)

    def _get_meta_dict(self, tt_lines):
        for line in tt_lines:
            if line.startswith("<meta"):
                return dict(re.findall(r'(?P<attr>[\w._-]+)="(?P<value>.*?)"', line))
        raise MetaNotFound(self.repo_path, self._current_text_contents.path)

    def _generate_visualizations_and_add_to_tx(self, text, contents):
        for config_name in HTML_CONFIGS:
            rendered_html = generate_visualization(
                config_name, contents
            )
            
            vis = HtmlVisualization()
            vis.visualization_format_slug = config_name
            
            vis.html = rendered_html
            self._current_transaction.add_vis((text, vis))

    def _scrape_text_and_add_to_tx(self, corpus, corpus_dirname, contents, tree_id, filename):
        tt_lines = contents.split("\n")
        meta = self._get_meta_dict(tt_lines)
        # FIXME: something called latest sounds dangerous.
        self._latest_meta_dict = meta
        text = Text()
        text.title = meta["title"]
        text.tt_dir=corpus_dirname
        text.tt_filename=filename
        text.tt_dir_tree_id=tree_id
        text.slug = slugify(meta["title"] if "title" in meta else meta["name"])
        text.corpus = self._current_corpus
        self._text_next[text.title] = meta["next"] if "next" in meta else None
        self._text_prev[text.title] = meta["previous"] if "previous" in meta else None
        self._text_urn[text.title] = (
            meta["document_cts_urn"] if "document_cts_urn" in meta else None
        )
        self.document_cts_urn=meta["document_cts_urn"]
        
        text_metas = [
            TextMeta(name=name, value=unescape(value)) for name, value in meta.items()
        ]
        # FIXME: here to finish the refactoring
        # we want to actually import the "tt" text rather than the visualisation
        # which we will do lazily (but it will make it easier to do FTS)
        self._generate_visualizations_and_add_to_tx(text, contents)
        self._current_transaction.add_text((text, text_metas))
