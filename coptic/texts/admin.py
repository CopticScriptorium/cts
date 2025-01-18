from django.contrib import admin
from texts.models import Corpus, Text, TextMeta, HtmlVisualization

admin.site.register(Corpus)
admin.site.register(Text)
admin.site.register(TextMeta)
admin.site.register(HtmlVisualization)
