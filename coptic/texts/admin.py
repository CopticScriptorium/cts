from django.contrib import admin
from texts.models import Corpus, Text, TextMeta, MetaOrder, HtmlVisualization


class MetaOrderAdmin(admin.ModelAdmin):
    list_display = ("name", "order")
    ordering = ("order",)


admin.site.register(Corpus)
admin.site.register(Text)
admin.site.register(TextMeta)
admin.site.register(MetaOrder, MetaOrderAdmin)

admin.site.register(HtmlVisualization)
