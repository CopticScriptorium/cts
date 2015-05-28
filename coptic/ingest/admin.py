from django.contrib import admin
from ingest.models import Ingest, ExpireIngest

admin.site.register(Ingest)
admin.site.register(ExpireIngest)
