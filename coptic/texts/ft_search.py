import meilisearch
from bs4 import BeautifulSoup
import re

from django.conf import settings

class Search():
    """
    A class for interacting with a MeiliSearch index to perform text searches and indexing operations.
    
    search_available (bool): Indicates if the search functionality is available.
    
    Methods:
    __init__():
        Initializes the MeiliSearch client and creates an index named "texts" with a primary key of 'id'.
        Sets up ranking rules if the index does not exist.
    index_text(texts):
        Adds documents to the MeiliSearch index. Takes a list of text objects where each object contains at least an 'id' and 'text' field.
    search(keyword):
        Performs a search query on the indexed texts using the provided keyword. It highlights matches within the 'text.lemmatized', 'text.normalized', and 'text.normalized_group' fields.
        Returns the search results with reduced text segments containing ellipses for better readability.
    faceted_search(keyword):
        Performs a faceted search query on the indexed texts using the provided keyword. It highlights matches within the 'text.lemmatized', 'text.normalized', and 'text.normalized_group' fields.
        Returns the search results with reduced text segments containing ellipses for better readability.
    reduce_search_result_with_ellipsis(search_results):
        Reduces the search result to a more manageable size by truncating text segments and adding ellipses.
        Processes the '_formatted' field in the search results to apply the reduction.
    reduce_text_with_ellipsis(html_text, n=10):
        Reduces the provided HTML text by keeping the first and last 'n' words and adding ellipses around highlighted segments.
    
    Attributes:
        client (meilisearch.Client): The MeiliSearch client object initialized with the server URL and master key.
        index (str): The name of the search index, defaulting to "texts".
        
    """
    def __init__(self):
        self.client = meilisearch.Client(settings.SEARCH_CONFIG['MEILI_HTTP_ADDR'],
                                         settings.SEARCH_CONFIG['MEILI_MASTER_KEY'])
        self.index = settings.SEARCH_CONFIG['MEILI_COPTIC_INDEX']
        # Create the index if it doesn't exist
        try:
            existing_indexes = self.client.get_indexes()['results']
            index_exists = any(idx.uid == self.index for idx in existing_indexes)
            if not index_exists:
                self.client.create_index(self.index, {'primaryKey': 'slug'})
                # FIXME: Update ranking rules
            self.client.index(self.index).update_settings({
            'rankingRules': [
                'exactness',
                'words',
                'typo',
                'proximity',
                'attribute',
                'sort',
            ],
            'distinctAttribute': 'slug',
            "filterableAttributes":
                         ['text_meta.corpus', 
                           'text_meta.author', 
                           'text_meta.people', 
                           'text_meta.places', 
                           'text_meta.msName', 
                           'text_meta.annotation', 
                           'text_meta.translation', 
                           'text_meta.arabic_translation',
                           ],
            "typoTolerance": {
                'minWordSizeForTypos': {
                    'oneTypo': 8,
                    'twoTypos': 10,
                    },
                'disableOnAttributes': ['text.english_translation']
                },
            #'searchableAttributes': [
            #    'title',
            #    'overview',
            #    'genres'
            #],
            #'displayedAttributes': [
            #    'title',
            #    'overview',
            #    'genres',
            #    'release_date'
            #],
            #'sortableAttributes': [
            #    'title',
            #    'release_date'
            #],
            #'stopWords': [
            #    'the',
            #    'a',
            #    'an'
            #],
            #'synonyms': {
            #    'wolverine': ['xmen', 'logan'],
            #    'logan': ['wolverine']
            #},
            #'typoTolerance': {
            #    'minWordSizeForTypos': {
            #        'oneTypo': 8,
            #        'twoTypos': 10
            #    },
            #    'disableOnAttributes': ['title']
            #},
            'pagination': {
                'maxTotalHits': 5000
            },
            'faceting': {
                'maxValuesPerFacet': 200
            },
            'searchCutoffMs': 150
            })
            self.search_available=True
        except:
            self.search_available=False
            pass

    def index_text(self, texts):
        return self.client.index(self.index).add_documents(texts)
    
    def delete_all_documents_index(self):
        return self.client.index(self.index).delete_all_documents()
    
    def delete_index(self):
        return self.client.index(self.index).delete()
    
    def search(self, keyword):
        results = self.client.index(self.index).search(keyword, {'showMatchesPosition': True, 'attributesToHighlight': ['text.lemmatized','text.normalized' ,'text.normalized_group', 'text.english_translation'], 'highlightPreTag': '<span class="highlight">','highlightPostTag': '</span>'})
        reduced_results = self.reduce_search_result_with_ellipsis(results)
        return reduced_results
    
    def faceted_search(self, keyword):
        results = self.client.index(self.index).search(keyword, {
            'showMatchesPosition': True, 
            'attributesToHighlight': 
                ['text.lemmatized','text.normalized' ,'text.normalized_group','text.english_translation'],
                'highlightPreTag': '<span class="highlight">',
                'highlightPostTag': '</span>',
                'facets': ['text_meta.corpus', 
                           'text_meta.author', 
                           'text_meta.people', 
                           'text_meta.places', 
                           'text_meta.msName', 
                           'text_meta.annotation', 
                           'text_meta.translation', 
                           'text_meta.arabic_translation'],          
                })
        reduced_results = self.reduce_search_result_with_ellipsis(results)
        return reduced_results

    def reduce_search_result_with_ellipsis(self, search_results):
        ### This function is used to reduce the search result to a more manageable size
        for hit in search_results['hits']:
            if '_formatted' in hit and 'text' in hit['_formatted']:
                for text_entry in hit['_formatted']['text']:
                    if 'lemmatized' in text_entry:
                        text_entry['lemmatized'] = self.reduce_text_with_ellipsis(text_entry['lemmatized'])
                    if 'normalized' in text_entry:
                        text_entry['normalized'] = self.reduce_text_with_ellipsis(text_entry['normalized'])
                    if 'normalized_group' in text_entry:
                        text_entry['normalized_group'] = self.reduce_text_with_ellipsis(text_entry['normalized_group'])
                    if 'english_translation' in text_entry:
                        text_entry['english_translation'] = self.reduce_text_with_ellipsis(text_entry['english_translation'])
        
        return search_results
    
    """
    Reduces the given HTML text to a more manageable size by keeping the highlighted text
    and a specified number of surrounding words, and replacing the rest with ellipses. 
    When context_size=0 the function will only keep the highlighted text and remove the rest.
    It always keeps the first and last words of the text (based on context_size)
    All
    FIXME: currently this is actually horribly inefficient. Specifically the part at the end
    where we add the first and last words.

    Parameters:
    html_text (str): The HTML text containing highlighted spans.
    context_size (int): The number of words to keep around each highlighted span. Default is 5.

    Returns:
    str: The reduced text with ellipses indicating omitted content.

    Example:
    >>> html_text = '<p>This is a very good <span class="highlight">test</span> case with a sentence with a highlight.</p>'
    >>> reduce_text_with_ellipsis(html_text, 2)
    'This is [...] very good <span class="highlight">test</span> case with [...] a highlight.'
    """
    def reduce_text_with_ellipsis(self, html_text, context_size=5):
        # Parse the HTML content
        CLEANR = re.compile('<.*?>') # Regex to remove HTML tags
        soup = BeautifulSoup(html_text, 'html.parser')
        
        # Extract all highlighted spans
        highlighted = soup.find_all('span', {'class': 'highlight'})
        if not highlighted:
            return soup.get_text()  # No highlights, return plain text
        
        # Collect highlighted text and surrounding context
        output_segments = []
        text = soup.get_text()
        words = text.split()
        
        # Always keep the first n and last n words
        first_3_words = " ".join(words[:3]) if context_size > 0 else ""
        last_3_words = " ".join(words[-3:]) if context_size > 0 else ""
        
        last_match_end = 0

        for span in highlighted:
            highlighted_text = span.get_text()
            match = re.search(re.escape(highlighted_text), text[last_match_end:])
            if not match:
                continue

            # Adjust match positions relative to the full text
            match_start = last_match_end + match.start()
            match_end = last_match_end + match.end()
            last_match_end = match_end

            # Calculate word boundaries for context
            start_idx = len(text[:match_start].split())  # Start word index
            end_idx = start_idx + len(highlighted_text.split())  # End word index

            # Extract context
            context_start = max(start_idx - context_size, 0)
            context_end = min(end_idx + context_size, len(words))
            context = " ".join(words[context_start:context_end])

            # Highlight the matched text in the context
            highlighted_context = context.replace(highlighted_text, f'<span class="highlight">{highlighted_text}</span>')

            # Append unique context to output_segments
            if highlighted_context not in output_segments:
                output_segments.append(highlighted_context)

        # Combine segments with ellipsis
        result = ' [...] '.join(output_segments)

        # Let's add the first two and last words of each text
        # If they are not within our context
        # FIXME this breaks if the result is in the first 
        # two words becaue of highlighting - we will be repeating
        # it. 
        
        cleanresult = re.sub(CLEANR, '', result)
        if first_3_words and first_3_words !=cleanresult[:len(first_3_words)]:
            result = ' [...] '.join([first_3_words, result])
        if last_3_words and last_3_words !=cleanresult[-len(last_3_words):]:
            result = ' [...] '.join([result, last_3_words])        
        return result

