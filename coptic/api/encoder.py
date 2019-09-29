'Encode corpora and texts for the front end'

from texts.models import MetaOrder


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


def _text_meta(text):
	meta_orders_by_name = {mo.name: mo.order for mo in MetaOrder.objects.all()}

	def order(name):
		return meta_orders_by_name.get(name) or 1000000

	sorted_metas = sorted(text.text_meta.all(), key=lambda m: order(m.name))

	return [{
		'name':             text_meta.name,
		'value':            text_meta.value,
		'value_customized': text_meta.value_customized()
	} for text_meta in sorted_metas]


def encode_text(text):
	return {
		'id':           text.id,
		'title':        text.title,
		'slug':         text.slug,
		'html_visualizations': _visualizations(text),
		'text_meta':    _text_meta(text),
		'corpus':       encode_corpus(text.corpus)
	}


def encode_corpus(corpus):
	encoded = {
		'title':              corpus.title,
		'urn_code':           corpus.urn_code,
		'slug':               corpus.slug,
		'annis_link':         corpus.annis_link(),
		'annis_corpus_name':  corpus.annis_corpus_name,
		'github':             corpus.github,
		'github_tei':         corpus.github_tei,
		'github_relannis':    corpus.github_relannis,
		'github_paula':       corpus.github_paula,
		'html_visualization_formats': _vis_formats(corpus)}

	if hasattr(corpus, 'texts'):
		encoded['texts'] = [{
			'id':       text.id,
			'title':    text.title,
			'slug':     text.slug
		} for text in corpus.texts]

	return encoded
