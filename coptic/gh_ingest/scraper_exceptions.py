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

class LocalTTDirMissing(Exception):
    def __init__(self, corpus_dirname, local_repo_path, tt_dir):
        self.corpus_dirname = corpus_dirname
        self.local_repo_path = local_repo_path
        self.tt_dir = tt_dir
        super().__init__(f"TT directory missing for corpus '{corpus_dirname}' in '{local_repo_path}'. Expected directory: '{tt_dir}'")

class ResolverVisMapIssue(ScraperException):
	"""Raised when the corpus's resolver_vis_map.annis is missing or malformed"""
	def __init__(self, corpus_dirname, repo_owner, repo_name, annis_dir):
		repo = repo_owner + "/" + repo_name
		url = f"https://github.com/{repo}/tree/master/{corpus_dirname}/{annis_dir}"
		self.message = (f"resolver_vis_map.annis in {annis_dir} for corpus '{corpus_dirname}' is either missing or "
						f"malformed."
						f"\n\tCheck the contents of {url} and make sure there's a file called 'resolver_vis_map.annis', "
						f"and that it is not malformed.")

	def __str__(self):
		return self.message


class VisConfigIssue(ScraperException):
	"""Raised when a visualization config is missing or malformed"""
	def __init__(self, config_path, repo_owner, repo_name):
		repo = repo_owner + "/" + repo_name
		url = f"https://github.com/{repo}/tree/master/{config_path}"
		self.message = (f"The visualization config file at {url} is either missing or malformed."
						f"\n\tCheck that {url} exists and is not malformed.")

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

class LocalMetaNotFound(ScraperException):
	"""Raised when text metadata couldn't be found"""
	def __init__(self, local_repo_path, _current_text_contents):
	
		self.message = (f"Could not find metadata in text '{_current_text_contents}'."
						f"\n\tCheck the contents of {local_repo_path} and make sure the text has a <meta> element.")

	def __str__(self):
		return self.message


class LocalScraperException(BaseException):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class LocalCorpusNotFound(LocalScraperException):
    """Raised when the LocalCorpusScraper attempts to read a corpus that doesn't exist."""
    def __init__(self, corpus_dirname, local_repo_path):
        self.message = f"Could not find corpus '{corpus_dirname}' in local repository at '{local_repo_path}'."
        super().__init__(self.message)

    def __str__(self):
        return self.message


class LocalEmptyCorpus(LocalScraperException):
    """Raised when a corpus exists but doesn't have directories ending in _TEI, _ANNIS, or _PAULA"""
    def __init__(self, corpus_dirname, local_repo_path):
        self.message = (f"Corpus '{corpus_dirname}' doesn't appear to have any directories ending in "
                        f"'_TEI', '_ANNIS', or '_PAULA' in local repository at '{local_repo_path}'.")
        super().__init__(self.message)

    def __str__(self):
        return self.message


class LocalAmbiguousCorpus(LocalScraperException):
    """Raised when more than one dir ends with _TEI, _RELANNIS, or _PAULA"""
    def __init__(self, corpus_dirname, local_repo_path):
        self.message = (f"Corpus '{corpus_dirname}' has one or more directories that end with "
                        f"_TEI, _ANNIS, or _PAULA in local repository at '{local_repo_path}'.")
        super().__init__(self.message)

    def __str__(self):
        return self.message


class LocalInferenceError(LocalScraperException):
    """Raised when no known inference strategy works for recovering some piece of information."""
    def __init__(self, corpus_dirname, local_repo_path, attr):
        self.message = (f"Failed to infer '{attr}' for '{corpus_dirname}' in local repository at '{local_repo_path}'.")
        super().__init__(self.message)

    def __str__(self):
        return self.message


class LocalTTDirMissing(LocalScraperException):
    """Raised when the corpus's _TT directory is missing"""
    def __init__(self, corpus_dirname, local_repo_path, tt_dir):
        self.message = (f"Could not find a _TT directory at '{tt_dir}' for corpus '{corpus_dirname}' in local repository at '{local_repo_path}'.")
        super().__init__(self.message)

    def __str__(self):
        return self.message


class LocalResolverVisMapIssue(LocalScraperException):
    """Raised when the corpus's resolver_vis_map.annis is missing or malformed"""
    def __init__(self, corpus_dirname, local_repo_path, annis_dir):
        self.message = (f"resolver_vis_map.annis in '{annis_dir}' for corpus '{corpus_dirname}' is either missing or malformed in local repository at '{local_repo_path}'.")
        super().__init__(self.message)

    def __str__(self):
        return self.message


class LocalVisConfigIssue(LocalScraperException):
    """Raised when a visualization config is missing or malformed"""
    def __init__(self, config_path, local_repo_path):
        self.message = (f"The visualization config file at '{config_path}' is either missing or malformed in local repository at '{local_repo_path}'.")
        super().__init__(self.message)

    def __str__(self):
        return self.message


class LocalNoTexts(LocalScraperException):
    """Raised when a corpus has no texts"""
    def __init__(self, corpus_dirname, local_repo_path, tt_dir):
        self.message = (f"Found a _TT directory at '{tt_dir}' for corpus '{corpus_dirname}', but it is empty in local repository at '{local_repo_path}'.")
        super().__init__(self.message)

    def __str__(self):
        return self.message


class LocalMetaNotFound(LocalScraperException):
    """Raised when text metadata couldn't be found"""
    def __init__(self, local_repo_path, file_path):
        self.message = (f"Could not find metadata in text '{file_path}' in local repository at '{local_repo_path}'.")
        super().__init__(self.message)

    def __str__(self):
        return self.message