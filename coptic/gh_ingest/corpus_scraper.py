from html import unescape
from collections import defaultdict
import re
import csv
from io import StringIO
from django.conf import settings
from django.db import transaction
from django.utils.text import slugify
from tqdm import tqdm
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
import csv

class CorpusScraper:
    def __init__(self):

        self._current_corpus = None
        self._current_transaction = None
        self._current_text_contents = None
        self._latest_meta_dict = None
        self._vis_configs = {}
        self._vis_config_contents = {}

        self._text_next = defaultdict(lambda: None)
        self._text_prev = defaultdict(lambda: None)
        self._text_urn = defaultdict(lambda: None)


    def parse_corpora(self, corpus_dirnames):
        corpora = []
        for corpus_dirname in corpus_dirnames:
            corpora.append(self.parse_corpus(corpus_dirname))
        return corpora

    def _infer_dirs(self, corpus, corpus_dirname):
        dirs = corpus.repository._get_dirs(corpus_dirname)    
        def find_dir(suffix):
            matched_dirs = [d for d in dirs if suffix in d]
            if len(matched_dirs) > 1:
                raise AmbiguousCorpus(corpus.slug, self.repo_path)
            return matched_dirs[0] if matched_dirs else ""

        tei = find_dir("_TEI")
        relannis = find_dir("ANNIS")
        paula = find_dir("_PAULA")

        if not (tei or relannis or paula):
            raise EmptyCorpus(corpus_dirname, settings.LOCAL_REPO_PATH)

        return tei, relannis, paula

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
                    corpus.repository.repo_path,
                    corpus_dirname,
                    corpus.github_relannis,
                )
        try:
            if corpus.github_relannis.endswith("zip"):
                vm = corpus.repository._get_zip_file_contents(vm_path, file_name)
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
    
        corpus = Corpus()
        if corpus_dirname not in corpus.repository._corpora:
            raise CorpusNotFound(corpus_dirname, self.repo_path)

        self._current_corpus = corpus
        self._current_transaction = CorpusTransaction(corpus_dirname, corpus)

        github_url = f"https://github.com/{corpus.repository.corpus_repo_owner}/{corpus.repository.corpus_repo_name}/tree/master/{corpus_dirname}"
        print(f"Processing '{github_url}' from '{corpus.repository.repo_path}'...")
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
        # If this corpus has a slug in the settings, use it
        if settings.CORPUS_MAP[corpus.annis_corpus_name].get("slug", None):
            corpus.slug = settings.CORPUS_MAP[corpus.annis_corpus_name]["slug"]
            print(f"Found slug for '{corpus.annis_corpus_name}': '{corpus.title}'")
        else:
            corpus.slug = slugify(corpus.annis_corpus_name)
        # If this corpus has a title in the settings, use it
        if settings.CORPUS_MAP[corpus.annis_corpus_name].get("title", None):
            corpus.title = settings.CORPUS_MAP[corpus.annis_corpus_name]["title"]
            print(f"Found title for '{corpus.annis_corpus_name}': '{corpus.title}'")
        else:
            corpus.title = corpus.annis_corpus_name
            print(f"Title not found for '{corpus.annis_corpus_name}'. Using '{corpus.title}'")

        self._current_transaction.add_vis_formats(
            self._infer_html_visualization_formats_and_add_to_tx(corpus, corpus_dirname)
        )

        texts, tree_id = corpus.repository._get_texts(corpus, corpus_dirname)
        self._scrape_texts_and_add_to_tx(corpus, corpus_dirname, texts, tree_id)
        self._current_transaction.sort_texts(
            self._text_next, self._text_prev, self._text_urn
        )

        # first prefer the explicit map
        if settings.CORPUS_MAP[corpus.annis_corpus_name].get("urn", None):
            corpus.urn_code = settings.CORPUS_MAP[corpus.annis_corpus_name]["urn"]
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
        for config_name in settings.HTML_CONFIGS:
            if settings.LAZY_HTML_GENERATION:
                rendered_html = ""
            else:
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