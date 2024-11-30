from django.contrib import admin
from texts.models import Corpus, Text, TextMeta, MetaOrder, HtmlVisualization


@admin.register(MetaOrder)
class MetaOrderAdmin(admin.ModelAdmin):
    list_display = ("name", "order")
    ordering = ("order",)


admin.site.register(Corpus)
admin.site.register(Text)
admin.site.register(TextMeta)

admin.site.register(HtmlVisualization)
