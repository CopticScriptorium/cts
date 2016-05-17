"""
Define custom encoder for the queryset model class instances
"""
from texts.models import Text, Corpus, HtmlVisualizationFormat


class Encoder:

    def __init__(self):
        self.vis_formats = {vf.id: vf for vf in HtmlVisualizationFormat.objects.all()}
        self.texts = {t.id: t for t in Text.objects.all().prefetch_related(
            'text_meta', 'html_visualizations', 'html_visualizations__visualization_format')}

    def _visualizations(self, obj):
        cached_text = self.texts[obj.id]
        return [{
            "title":    v.visualization_format.title,
            "slug":     v.visualization_format.slug,
            "html":     v.html
        } for v in cached_text.html_visualizations.all()]

    def _vis_formats(self, obj):
        return [{
            'title':        vf.title,
            'button_title': vf.button_title,
            'slug':         vf.slug
        } for vf in obj.html_visualization_formats.all()]

    def _text_meta(self, obj):
        cached_text = self.texts[obj.id]
        return [{
            'name':  text_meta.name,
            'value': text_meta.value_with_urls_wrapped()
        } for text_meta in cached_text.text_meta.all()]

    def encode(self, obj):

        # If we're dumping an instance of the Text class to JSON
        if isinstance(obj, Text):
            return {
                'id':           obj.id,
                'title':        obj.title,
                'slug':         obj.slug,
                'is_expired':   obj.is_expired,
                'html_visualizations': self._visualizations(obj),
                'text_meta':    self._text_meta(obj),
                'corpus':       self.encode(obj.corpus)
            }

        # If we're dumping an instance of the Corpus class to JSON
        if isinstance(obj, Corpus):
            corpus = {
                'title':              obj.title,
                'urn_code':           obj.urn_code,
                'slug':               obj.slug,
                'annis_link':         obj.annis_link(),
                'annis_corpus_name':  obj.annis_corpus_name,
                'github':             obj.github,
                'html_visualization_formats': self._vis_formats(obj)}

            if hasattr(obj, 'texts'):
                corpus['texts'] = [{
                    'id':       text.id,
                    'title':    text.title,
                    'slug':     text.slug,
                    'html_visualizations': self._visualizations(text)
                } for text in obj.texts]

            return corpus
