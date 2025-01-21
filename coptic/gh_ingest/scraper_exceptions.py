class ScraperException(BaseException):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return self.message


class TTDirMissing(ScraperException):
    def __init__(self, corpus_dirname, local_repo_path, tt_dir):
        message = f"TT directory missing for corpus '{corpus_dirname}' in '{local_repo_path}'. Expected directory: '{tt_dir}'"
        super().__init__(message)


class MetaNotFound(ScraperException):
    """Raised when text metadata couldn't be found"""

    def __init__(self, local_repo_path, _current_text_contents):
        message = (
            f"Could not find metadata in text '{_current_text_contents}'."
            f"\n\tCheck the contents of {local_repo_path} and make sure the text has a <meta> element."
        )
        super().__init__(message)


class CorpusNotFound(ScraperException):
    """Raised when the CorpusScraper attempts to read a corpus that doesn't exist."""

    def __init__(self, corpus_dirname, local_repo_path):
        message = f"Could not find corpus '{corpus_dirname}' in local repository at '{local_repo_path}'."
        super().__init__(message)


class EmptyCorpus(ScraperException):
    """Raised when a corpus exists but doesn't have directories ending in _TEI, _ANNIS, or _PAULA"""

    def __init__(self, corpus_dirname, local_repo_path):
        message = (
            f"Corpus '{corpus_dirname}' doesn't appear to have any directories ending in "
            f"'_TEI', '_ANNIS', or '_PAULA' in local repository at '{local_repo_path}'."
        )
        super().__init__(message)


class AmbiguousCorpus(ScraperException):
    """Raised when more than one dir ends with _TEI, _RELANNIS, or _PAULA"""

    def __init__(self, corpus_dirname, local_repo_path):
        message = (
            f"Corpus '{corpus_dirname}' has one or more directories that end with "
            f"_TEI, _ANNIS, or _PAULA in local repository at '{local_repo_path}'."
        )
        super().__init__(message)


class InferenceError(ScraperException):
    """Raised when no known inference strategy works for recovering some piece of information."""

    def __init__(self, corpus_dirname, local_repo_path, attr):
        message = f"Failed to infer '{attr}' for '{corpus_dirname}' in local repository at '{local_repo_path}'."
        super().__init__(message)


class GetFileContentIssue(ScraperException):
    """Raised when we can't grab a corpus file config or css file"""

    def __init__(self, corpus_dirname, local_repo_path, annis_dir):
        message = f"Getting file content failed in '{annis_dir}' for corpus '{corpus_dirname}' is either missing or malformed in local repository at '{local_repo_path}'."
        super().__init__(message)

class ResolverVisMapIssue(ScraperException):
    """Raised when the corpus's resolver_vis_map.annis is missing or malformed"""

    def __init__(self, corpus_dirname, local_repo_path, annis_dir):
        message = f"resolver_vis_map.annis in '{annis_dir}' for corpus '{corpus_dirname}' is either missing or malformed in local repository at '{local_repo_path}'."
        super().__init__(message)


class VisConfigIssue(ScraperException):
    """Raised when a visualization config is missing or malformed"""

    def __init__(self, config_path, local_repo_path):
        message = f"The visualization config file at '{config_path}' is either missing or malformed in local repository at '{local_repo_path}'."
        super().__init__(message)


class NoTexts(ScraperException):
    """Raised when a corpus has no texts"""

    def __init__(self, corpus_dirname, local_repo_path, tt_dir):
        message = f"Found a _TT directory at '{tt_dir}' for corpus '{corpus_dirname}', but it is empty in local repository at '{local_repo_path}'."
        super().__init__(message)
