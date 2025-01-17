from io import BytesIO
import logging
import os
import subprocess
import zipfile
from gh_ingest.scraper_exceptions import NoTexts, TTDirMissing

from django.conf import settings
from cache_memoize import cache_memoize

# This is a singleton class that will be used to store the repository
# it will be used to store the repository and the corpora in it.
class SingletonMeta(type):
    """
    A Singleton metaclass that ensures a class has only one instance.
    """
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]

class Repository(metaclass=SingletonMeta):
    def __init__(self):
        """
        Initializes the Repository instance.

        This constructor sets up the initial configuration for the CorpusScraper,
        ensures the local repository is available, and initializes various attributes
        related to the corpus and visualization formats.

        Attributes:
            corpus_repo_name (str): The name of the corpus repository.
            corpus_repo_owner (str): The owner of the corpus repository.
            repo_path (str): The local path to the repository.
            _corpora (list): A list of directories in the local repository path that represent corpora.
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
        
    def ensure_repo(self):
        if not os.path.exists(os.path.join(self.repo_path, ".git")):
            self.clone_repo()
        else:
            self.pull_repo()

    def clone_repo(self):
        try:
            repo_url = f"https://github.com/{self.corpus_repo_owner}/{self.corpus_repo_name}.git"
            subprocess.run(["git", "clone", "--depth", "1", repo_url, self.repo_path], check=True) # we should do a shallow clone.
            logging.info(f"Cloned repository from {repo_url} to {self.repo_path}")
        except:
            logging.info(f"Could not clone repository from probably offline, but do please check the error")

    def pull_repo(self):
        try:
            subprocess.run(["git", "-C", self.repo_path, "pull"], check=True)
            logging.info(f"Pulled latest changes in repository at {self.repo_path}")
        except:
            logging.info(f"Could not pull repository from  upstream probably offline")

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
                self.corpus_repo_owner = settings.CORPUS_REPO_OWNER
        except:
            logging.warning("CORPUS_REPO_OWNER not found in settings. Using default value CopticScriptorium.")
            self.corpus_repo_owner = "CopticScriptorium"
        try: 
            if not self.corpus_repo_name:
                self.corpus_repo_name = settings.CORPUS_REPO_NAME
        except:
            logging.warning("CORPUS_REPO_NAME not found in settings. Using default value corpora.")
            self.corpus_repo_name = "corpora"
        try:
            if not self.repo_path:
                self.repo_path = settings.LOCAL_REPO_PATH
        except:
            logging.warning("LOCAL_REPO_PATH not found in settings. Using default value ../../corpora.")
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
    
    def _get_dirs(self, corpus_dirname):    
        corpus_path = os.path.join(self.repo_path, corpus_dirname)
        return [name for name in os.listdir(corpus_path) if os.path.isdir(os.path.join(corpus_path, name)) or name.endswith(".zip")]
    
    # This is an expensive operation we also call from get_text()
    # so caching it.
    @cache_memoize(settings.CACHE_TTL)
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