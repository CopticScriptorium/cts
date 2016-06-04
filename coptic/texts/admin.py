from django.contrib import admin
from texts.models import Corpus, Text, TextMeta, SearchField, SearchFieldValue, HtmlVisualization, HtmlVisualizationFormat

admin.site.register(Corpus)
admin.site.register(Text)
admin.site.register(TextMeta)
admin.site.register(SearchField)
admin.site.register(SearchFieldValue)
admin.site.register(HtmlVisualization)
admin.site.register(HtmlVisualizationFormat)
