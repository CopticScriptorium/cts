# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ingest', '0003_ingest_corpora'),
    ]

    operations = [
        migrations.AddField(
            model_name='ingest',
            name='num_corpora_ingested',
            field=models.PositiveIntegerField(default=0),
        ),
    ]
