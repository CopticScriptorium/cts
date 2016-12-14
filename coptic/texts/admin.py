from django.contrib import admin
from texts.models import Corpus, Text, TextMeta, MetaOrder, SpecialMeta, \
	HtmlVisualization, HtmlVisualizationFormat

class MetaOrderAdmin(admin.ModelAdmin):
	list_display = ('name', 'order')
	ordering = ('order', )

admin.site.register(Corpus)
admin.site.register(Text)
admin.site.register(TextMeta)
admin.site.register(MetaOrder, MetaOrderAdmin)
admin.site.register(SpecialMeta)
admin.site.register(HtmlVisualization)
admin.site.register(HtmlVisualizationFormat)
