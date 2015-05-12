"""
Define custom encoder for the queryset model class instances
"""
import json
from texts.models import Text, Corpus, SearchFieldValue, HtmlVisualization, HtmlVisualizationFormat, TextMeta


def coptic_encoder( obj ):

	encoded = {}

	# If we're dumping an instance of the Text class to JSON
	if isinstance(obj, Text):
		text = {}

		text['title'] = obj.title 
		text['slug'] = obj.slug 
		text['html_visualizations'] = []
		text['text_meta'] = []

		for text_meta in obj.text_meta.all(): 
			if text_meta.name == "msName":
				text['msName'] = text_meta.value.replace(".", "-")

			text['text_meta'].append({
					'name' : text_meta.name,
					'value' : text_meta.value 
				})

		for html_visualization in obj.html_visualizations.all():
			text['html_visualizations'].append({
					"title" : html_visualization.visualization_format.title,
					"slug" : html_visualization.visualization_format.slug,
					"html" : html_visualization.html
				})

		text['corpus'] = coptic_encoder( obj.corpus )

		encoded = text

	# If we're dumping an instance of the Corpus class to JSON
	elif isinstance(obj, Corpus):
		corpus = {}

		corpus['title'] = obj.title 
		corpus['urn_code'] = obj.urn_code 
		corpus['slug'] = obj.slug 
		corpus['annis_code'] = obj.annis_code 
		corpus['annis_corpus_name'] = obj.annis_corpus_name
		corpus['github'] = obj.github 
		corpus['html_visualization_formats'] = []

		for html_visualization_format in obj.html_visualization_formats.all():
			corpus['html_visualization_formats'].append({
					'title' : html_visualization_format.title,
					'button_title' : html_visualization_format.button_title,
					'slug' : html_visualization_format.slug
				}) 

		if hasattr(obj, 'texts'):
			corpus['texts'] = []
			for i, text in enumerate( obj.texts ):
				corpus['texts'].append({
						'id' : text.id,
						'title' : text.title,
						'slug' : text.slug,
						'html_visualizations' : [] 
					})
				for html_visualization in text.html_visualizations.all():
					corpus['texts'][ i ]['html_visualizations'].append({
							"title" : html_visualization.visualization_format.title,
							"slug" : html_visualization.visualization_format.slug
						})

		encoded = corpus

	return encoded 


