import meilisearch
from django.conf import settings

class Search():
    """
    A class for interacting with a MeiliSearch index to perform text searches and indexing operations.
    
    Attributes:
        client (meilisearch.Client): The MeiliSearch client object initialized with the server URL and master key.
        index (str): The name of the search index, defaulting to "texts".
        
    Methods:
        __init__(): Initializes the MeiliSearch client and creates an index named "texts" with a primary key of 'id'.
        index_text(texts): Adds documents to the MeiliSearch index. Takes a list of text objects where each object contains at least an 'id' and 'text' field.
        search(keyword): Performs a search query on the indexed texts using the provided keyword. It highlights matches within the 'text.lemmatized' and 'text.normalized' fields.
    """
    def __init__(self):
        self.client = meilisearch.Client(settings.SEARCH_CONFIG['MEILISEARCH_URL'],settings.SEARCH_CONFIG['MEILISEARCH_MASTER_KEY'])
        self.index = settings.SEARCH_CONFIG['MEILISEARCH_INDEX']
        # Create the index if it doesn't exist
        existing_indexes = self.client.get_indexes()['results']
        index_exists = any(idx.uid == self.index for idx in existing_indexes)
        if not index_exists:
            self.client.create_index(self.index, {'primaryKey': 'id'})
        self.client.create_index(self.index, {'primaryKey': 'id'})
        pass
    
    def index_text(self, texts):
        return self.client.index(self.index).add_documents(texts)
    
    def search(self, keyword):
        return self.client.index(self.index).search(keyword, {'showMatchesPosition': True, 'attributesToHighlight': ['text.lemmatized','text.normalized'], 'highlightPreTag': '<span class="highlight">','highlightPostTag': '</span>'})
