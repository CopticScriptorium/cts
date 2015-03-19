# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ingest', '0003_ingestsearchfields'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='ingest',
            options={'verbose_name': 'Document Ingest', 'verbose_name_plural': 'Document Ingests'},
        ),
        migrations.AlterModelOptions(
            name='ingestsearchfields',
            options={'verbose_name': 'Search Field Ingest', 'verbose_name_plural': 'Search Field Ingests'},
        ),
    ]
