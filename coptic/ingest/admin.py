from django.contrib import admin
from ingest.models import Ingest, ExpireIngest


class IngestAdmin(admin.ModelAdmin):
    list_display = ('created', 'modified', 'num_corpora_ingested', 'num_texts_ingested')

admin.site.register(Ingest, IngestAdmin)
admin.site.register(ExpireIngest)
