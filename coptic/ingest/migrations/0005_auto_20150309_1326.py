# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ingest', '0004_auto_20150309_0253'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='ingest',
            options={'verbose_name': 'Document Ingest'},
        ),
        migrations.AlterModelOptions(
            name='ingestsearchfields',
            options={'verbose_name': 'Search Field Ingest'},
        ),
    ]
