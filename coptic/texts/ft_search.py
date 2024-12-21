import meilisearch

class Search():
    def __init__(self):
        self.client = meilisearch.Client('http://127.0.0.1:7700', 'masterKey')
        self.index="texts"
        self.client.create_index(self.index, {'primaryKey': 'id'})
        pass
    
    def index_text(self, texts):
        return self.client.index(self.index).add_documents(texts)
    
    def search(self, keyword):
        return self.client.index(self.index).search(keyword, {'showMatchesPosition': True, 'attributesToHighlight': ['html_visualizations.html'], 'highlightPreTag': '<span class="highlight">','highlightPostTag': '</span>'})
