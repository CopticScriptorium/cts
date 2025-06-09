from django.contrib import admin
from texts.models import Corpus, Text, TextMeta, HtmlVisualization

class TextInline(admin.TabularInline):
    model = Text
    extra = 1

class HtmlVisualizationInline(admin.TabularInline):
    model = Text.html_visualizations.through
    extra = 1

@admin.register(Corpus)
class CorpusAdmin(admin.ModelAdmin):
    inlines = [TextInline]
    list_display = [field.name for field in Corpus._meta.fields]

@admin.register(Text)
class TextAdmin(admin.ModelAdmin):
    filter_horizontal = ('text_meta', 'html_visualizations')
    list_display = [field.name for field in Text._meta.fields]
    inlines = [HtmlVisualizationInline]

@admin.register(TextMeta)
class TextMetaAdmin(admin.ModelAdmin):
    list_display = [field.name for field in TextMeta._meta.fields]

@admin.register(HtmlVisualization)
class HtmlVisualizationAdmin(admin.ModelAdmin):
    list_display = [field.name for field in HtmlVisualization._meta.fields]
