import meilisearch
from bs4 import BeautifulSoup
import re

from django.conf import settings


class Search:
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
        self.client = meilisearch.Client(
            settings.SEARCH_CONFIG["MEILI_HTTP_ADDR"],
            settings.SEARCH_CONFIG["MEILI_MASTER_KEY"],
        )
        self.index = settings.SEARCH_CONFIG["MEILI_COPTIC_INDEX"]
        # Create the index if it doesn't exist
        try:
            existing_indexes = self.client.get_indexes()["results"]
            index_exists = any(idx.uid == self.index for idx in existing_indexes)
            if not index_exists:
                self.client.create_index(self.index, {"primaryKey": "slug"})
                # FIXME: Update ranking rules
            self.client.index(self.index).update_settings(
                {
                    "rankingRules": [
                        "exactness",
                        "words",
                        "typo",
                        "proximity",
                        "attribute",
                        "sort",
                    ],
                    "distinctAttribute": "slug",
                    "filterableAttributes": [
                        "text_meta.corpus",
                        "text_meta.author",
                        "text_meta.people",
                        "text_meta.places",
                        "text_meta.msName",
                        "text_meta.annotation",
                        "text_meta.translation",
                        "text_meta.arabic_translation",
                    ],
                    "typoTolerance": {
                        "minWordSizeForTypos": {
                            "oneTypo": 8,
                            "twoTypos": 20,
                        },
                        "disableOnAttributes": [
                            #'text.lemmatized',
                            #'text.normalized',
                            #'text.normalized_group',
                        ],
                    },
                    "searchableAttributes": [
                        "title",
                        "corpus",
                        "author",
                        "text.lemmatized",
                        "text.normalized",
                        "text.normalized_group",
                        "text.english_translation",
                        "text.arabic_translation",
                        "text_meta.author",
                        "text_meta.annotation",
                        "text_meta.translation",
                        "text_meta.people",
                        "text_meta.places",
                        "text_meta.msName",
                        "text_meta.annotation",
                        "text_meta.translation",
                        "text_meta.collection",
                        "text_meta.country",
                        "text_meta.language",
                        "text_meta.note",
                        "text_meta.objectType",
                        "text_meta.origDate",
                        "text_meta.origDate_notAfter",
                        "text_meta.origPlace",
                        "text.meta.repository",
                        "text.meta.witness",
                    ],
                    "displayedAttributes": [
                        "title",
                        "corpus",
                        "author",
                        "slug",
                        "corpus_slug",
                        "text.lemmatized",
                        "text.normalized",
                        "text.normalized_group",
                        "text.english_translation",
                        "text.arabic_translation",
                        "text_meta.author",
                        "text_meta.document_cts_urn",
                        "text_meta.annotation",
                        "text_meta.translation",
                        "text_meta.people",
                        "text_meta.places",
                        "text_meta.msName",
                        "text_meta.annotation",
                        "text_meta.translation",
                        "text_meta.collection",
                        "text_meta.country",
                        "text_meta.language",
                        "text_meta.note",
                        "text_meta.objectType",
                        "text_meta.origDate",
                        "text_meta.origDate_notAfter",
                        "text_meta.origPlace",
                        "text_meta.repository",
                        "text_meta.witness",
                    ],
                    #'sortableAttributes': [
                    #    'title',
                    #    'release_date'
                    # ],
                    #'stopWords': [
                    #    'the',
                    #    'a',
                    #    'an'
                    # ],
                    #'synonyms': {
                    #    'wolverine': ['xmen', 'logan'],
                    #    'logan': ['wolverine']
                    # },
                    #'typoTolerance': {
                    #    'minWordSizeForTypos': {
                    #        'oneTypo': 8,
                    #        'twoTypos': 10
                    #    },
                    #    'disableOnAttributes': ['title']
                    # },
                    "pagination": {"maxTotalHits": 5000},
                    "faceting": {"maxValuesPerFacet": 400},
                    "searchCutoffMs": 400,
                }
            )
            self.search_available = True
        except:
            self.search_available = False
            pass

    def index_text(self, texts):
        return self.client.index(self.index).add_documents(texts)

    def delete_all_documents_index(self):
        return self.client.index(self.index).delete_all_documents()

    def delete_index(self):
        return self.client.index(self.index).delete()

    def search(self, keyword):
        return self.client.index(self.index).search(
            keyword,
            {
                "showMatchesPosition": True,
                "attributesToHighlight": [
                    "text.lemmatized",
                    "text.normalized",
                    "text.normalized_group",
                    "text.english_translation",
                ],
                "highlightPreTag": '<span class="highlight">',
                "highlightPostTag": "</span>",
                "cropLength": 100,
                "attributesToCrop": [
                    "text.lemmatized",
                    "text.normalized",
                    "text.normalized_group",
                    "text.english_translation",
                    "text.arabic_translation",
                ],
            },
        )

    def faceted_search(self, keyword, filters=None, page=1, hits_per_page=4):
        search_params = {
            "showMatchesPosition": True,
            "attributesToCrop": [
                "text.lemmatized",
                "text.normalized",
                "text.normalized_group",
                "text.english_translation",
                "text.arabic_translation",
            ],
            "cropLength": 100,
            "attributesToHighlight": [
                "title",
                "corpus",
                "author",
                "text.lemmatized",
                "text.normalized",
                "text.normalized_group",
                "text.english_translation",
                "text_meta.author",
                "text_meta.people",
                "text_meta.places",
            ],
            "highlightPreTag": '<span class="highlight">',
            "highlightPostTag": "</span>",
            "facets": [
                "text_meta.corpus",
                "text_meta.author",
                "text_meta.people",
                "text_meta.places",
                "text_meta.msName",
                "text_meta.annotation",
                "text_meta.translation",
                "text_meta.arabic_translation",
            ],
            "page": page,
            "hitsPerPage": hits_per_page,
        }
        if filters:
            search_params["filter"] = filters

        return self.client.index(self.index).search(keyword, search_params)
