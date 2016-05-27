"""
Define custom encoder for the queryset model class instances
"""
from texts.models import Text, Corpus

def _visualizations(obj):
	return [{
		"title":    v.visualization_format.title,
		"slug":     v.visualization_format.slug,
		"html":     v.html
	} for v in obj.html_visualizations.all()]

def _vis_formats(obj):
	return [{
		'title':        vf.title,
		'button_title': vf.button_title,
		'slug':         vf.slug
	} for vf in obj.html_visualization_formats.all()]

def _text_meta(obj):
	return [{
		'name':             text_meta.name,
		'value':            text_meta.value,
		'value_customized': text_meta.value_customized()
	} for text_meta in obj.text_meta.all()]

def encode(obj):

	# If we're dumping an instance of the Text class to JSON
	if isinstance(obj, Text):
		return {
			'id':           obj.id,
			'title':        obj.title,
			'slug':         obj.slug,
			'is_expired':   obj.is_expired,
			'html_visualizations': _visualizations(obj),
			'text_meta':    _text_meta(obj),
			'corpus':       encode(obj.corpus)
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
			'github_tei':         obj.github_tei,
			'github_relannis':    obj.github_relannis,
			'github_paula':       obj.github_paula,
			'html_visualization_formats': _vis_formats(obj)}

		if hasattr(obj, 'texts'):
			corpus['texts'] = [{
				'id':       text.id,
				'title':    text.title,
				'slug':     text.slug
			} for text in obj.texts]

		return corpus
