from html import unescape
from collections import defaultdict
import logging
import re
import csv
from io import StringIO
from xml.dom import NotFoundErr
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
                raise AmbiguousCorpus(corpus.slug, settings.LOCAL_REPO_PATH)
            return matched_dirs[0] if matched_dirs else ""

        tei = find_dir("_TEI")
        relannis = find_dir("ANNIS")
        paula = find_dir("_PAULA")

        if not (tei or relannis or paula):
            raise EmptyCorpus(corpus_dirname, settings.LOCAL_REPO_PATH)

        return tei, relannis, paula

    def _infer_html_visualization_formats_and_add_to_tx(self, corpus, corpus_dirname):
        """
        Tnis file looks like the followingù ...
        pseudo.basil	NULL	scriptorium	node	grid	[... redacted from brevity ...]
        pseudo.basil	NULL	dep	edge	arch_dependency	syntax (dependencies)	hidden	2	node_key:norm
        pseudo.basil	NULL	NULL	NULL	htmldoc	normalized text (document)	hidden	102	config:verses
        pseudo.basil	NULL	NULL	NULL	htmldoc	analytic view (document)	hidden	101	config:analytic

        Args:
            corpus (_type_): _description_
            corpus_dirname (_type_): _description_

        Returns:
            _type_: _description_
        """
        
        vis_map_content = StringIO(self.get_file_content(corpus, corpus_dirname, "resolver_vis_map.annis"))
        reader = csv.reader(vis_map_content, delimiter="\t", lineterminator="\n")
        formats=[] # this is a list because we want them unique
        for row in reader:
            if row[4]=="htmldoc": # if the fourth column is htmldoc
                #FIXME: we actually want the button_title 
                # This is very hacky so we are doing it step by step for clarity
                # We take the fifth column, of the format "diplomatic text (document)"
                # and we split it by spaces and take the first element
                title = row[5]
                title = title.split(" ")[0]
                # vis_type= row[8].split("config:")[1] # extract the format type 
                # FIXME: Now the problem is that the actual config files for norm/normalized
                # are going to have different names (verses). So need to figure out how to
                # pass that. Probably the simplest is to add to HTML_VISUALISATION_FORMATS
                # something like config_file_name=verses if we can be sure it  is systematic.
                format = HtmlVisualization.get_format_by_attribute( "button_title", title)
                if format and format not in formats:
                    formats.append(format)
                else:
                    logging.error(f"Seeing format for the second time '{format.slug}'")
        return formats

    def get_file_content(self, corpus, corpus_dirname, file_name):
        """ This loads files like ./pseudo-basil/pseudo.basil_ANNIS/resolver_vis_map.annis from
        the corpus repository. It will raise a ResolverVisMapIssue if the file is not found.
    
        Args:
            corpus (_type_): _description_
            corpus_dirname (_type_): _description_

        Raises:
            ResolverVisMapIssue: _description_

        Returns:
            _type_: _description_
        """
        
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
            raise GetFileContentIssue(
                corpus_dirname, settings.LOCAL_REPO_PATH, corpus.github_relannis
            ) from e
            
        return vm

    def get_vis_config_file(self, corpus, corpus_dirname, config_file, zip_file):
        try:
            if zip_file:
                path = "ExtData/" + config_file + ".config"
                return zip_file.open(path).read().decode('utf-8')
            else:
                # FIXME we should use os.path.join here
                path = os.path.join(corpus_dirname, corpus.github_relannis , "ExtData/" + config_file + ".config")
                f = self._repo.file_contents(path)
                return f.decoded.decode('utf-8')
        except NotFoundErr as e:
            raise VisConfigIssue(path, self.corpus_repo_owner, self.corpus_repo_name) from e
        
    @transaction.atomic
    def parse_corpus(self, corpus_dirname):
    
        corpus = Corpus(read_repository=True)
        if corpus_dirname not in corpus.repository._corpora:
            raise CorpusNotFound(corpus_dirname, settings.LOCAL_REPO_PATH)

        self._current_corpus = corpus
        self._current_transaction = CorpusTransaction(corpus_dirname, corpus)

        github_url = f"https://github.com/{corpus.repository.corpus_repo_owner}/{corpus.repository.corpus_repo_name}/tree/master/{corpus_dirname}"
        logging.info(f"Processing '{github_url}' from '{corpus.repository.repo_path}'...")
        existing_corpus = Corpus.objects.filter(github=github_url).first()

        # FIXME actually everything is fast enough now
        # to reimport everything, every time. We would get 
        # rid of all of the transacation stuff - which 
        # will make it even faster. Blue green.
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
            logging.info(f"Found slug for '{corpus.annis_corpus_name}': '{corpus.title}'")
        else:
            corpus.slug = slugify(corpus.annis_corpus_name)
        # If this corpus has a title in the settings, use it
        if settings.CORPUS_MAP[corpus.annis_corpus_name].get("title", None):
            corpus.title = settings.CORPUS_MAP[corpus.annis_corpus_name]["title"]
            logging.info(f"Found title for '{corpus.annis_corpus_name}': '{corpus.title}'")
        else:
            corpus.title = corpus.annis_corpus_name
            logging.info(f"Title not found for '{corpus.annis_corpus_name}'. Using '{corpus.title}'")

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
            logging.info(f"Found URN for '{corpus.annis_corpus_name}': '{corpus.urn_code}' in settings")
        # then if we have no meta or we don't have document_cts_urn set the urn code to empty
        elif self._latest_meta_dict is None or "document_cts_urn" not in self._latest_meta_dict:
            logging.warning(f"No URN found for '{corpus.annis_corpus_name}'. Setting to empty.")
            corpus.urn_code = ""
        # Finally set the urn code to whatever is in _latest_meta_dict
        # FIXME: figure out _latest_meta_dict
        else:
            logging.info(f"Setting URN for '{corpus.annis_corpus_name}' to '{self._latest_meta_dict['document_cts_urn']}' from meta")
            corpus.urn_code = urn.textgroup_urn(self._latest_meta_dict["document_cts_urn"])
        # lastly let's add the corpus author
        corpus.author = ', '.join(list(self._latest_meta_dict.get("author", [])))
        return self._current_transaction

    def _scrape_texts_and_add_to_tx(self, corpus, corpus_dirname, texts, tree_id):
        logging.info(f"Preparing transaction for '{corpus_dirname}'...")
        print(f"Preparing transaction for '{corpus_dirname}'...")
        for filename, contents in tqdm(texts.items(), ncols=80):
            if contents:
                self._current_text_contents = contents
                self._scrape_text_and_add_to_tx(corpus_dirname, contents, tree_id, filename, self._current_transaction._vis_formats)

    def _get_meta_dict(self, tt_lines):
        for line in tt_lines:
            if line.startswith("<meta"):
                return dict(re.findall(r'(?P<attr>[\w._-]+)="(?P<value>.*?)"', line))
        raise MetaNotFound(settings.LOCAL_REPO_PATH, self._current_text_contents.path)

    def _generate_visualizations_and_add_to_tx(self, corpus, corpus_dirname, text, vis_formats):
        for config in vis_formats:

            vis = HtmlVisualization()
            vis.visualization_format_slug = config["slug"]
            filename = config["slug"]
            
            #FIXME: for the time being if we meet norm we know its actually verses
            #TODO: Clearly we are not figuring out the correct css file .. or
            # we are not outputting the correct css.
            
            if filename=="norm":
                filename="verses"
            vis.config = self.get_file_content(corpus, corpus_dirname, "ExtData/" + filename + ".config")
            vis.css = self.get_file_content(corpus, corpus_dirname, "ExtData/" + filename + ".css")
            self._current_transaction.add_vis((text, vis))

    def _scrape_text_and_add_to_tx(self, corpus_dirname, contents, tree_id, filename, vis_formats):
        tt_lines = contents.split("\n"),
        # So here we can do the "splitting"
        meta = self._get_meta_dict(tt_lines[0])
        meta_split_and_cleaned= {}
        for key in meta:
            # these are the "special meta that might be splittable"
            if key in settings.METAS.keys():
                meta_split_and_cleaned[key]=  Text.split_and_clean_meta_values([meta[key]], settings.METAS[key])
            else:
                meta_split_and_cleaned[key]= meta[key]
        self._latest_meta_dict = meta_split_and_cleaned
        text = Text()
        text.content = contents
        text.title = meta["title"]
        text.tt_dir=corpus_dirname
        text.tt_filename=filename
        text.tt_dir_tree_id=tree_id # not yet used - but useful for doing partial imports, and general reproducibility
        text.slug = slugify(meta_split_and_cleaned["title"] if "title" in meta_split_and_cleaned else meta_split_and_cleaned["name"])
        text.corpus = self._current_corpus
        self._text_next[text.title] = meta_split_and_cleaned["next"] if "next" in meta_split_and_cleaned else None
        self._text_prev[text.title] = meta_split_and_cleaned["previous"] if "previous" in meta_split_and_cleaned else None
        self._text_urn[text.title] = (
            meta_split_and_cleaned["document_cts_urn"] if "document_cts_urn" in meta_split_and_cleaned else None
        )
        self.document_cts_urn=meta_split_and_cleaned["document_cts_urn"]
        
        if not self.document_cts_urn:
            raise "Missing URN"

        text_metas=[]
        for name in meta_split_and_cleaned:
            # If this is a string .. add once.
            if isinstance(meta_split_and_cleaned[name], str):
                # FIXME: I wonder what the unsescape is about.
                if name == "order":
                # put the order in the text model if it exists
                # Otherwise in the model it defaults to 99999 so
                # texts without an order will be at the bottom of the list
                    try:
                        text.order = int(meta_split_and_cleaned["order"])
                    except ValueError:
                        logging.warning(f"Found order '{meta_split_and_cleaned["order"]}'. But could not convert to int.")
                        # If order value can't be converted to int, keep default
                        pass
                text_metas.append(TextMeta(name=name, value=unescape(meta_split_and_cleaned[name])) )
            elif isinstance(meta_split_and_cleaned[name], list):
                for v in meta_split_and_cleaned[name]:
                    text_metas.append(
                        TextMeta(name=name, value=unescape(v)) 
                    )
            else:
                raise ("Unexpected type for meta value")
        
        self._generate_visualizations_and_add_to_tx( self._current_corpus, corpus_dirname, text, vis_formats)
        self._current_transaction.add_text((text, text_metas))