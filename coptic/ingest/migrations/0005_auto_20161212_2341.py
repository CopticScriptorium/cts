# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ingest', '0004_ingest_num_corpora_ingested'),
    ]

    operations = [
        migrations.AddField(
            model_name='ingest',
            name='num_texts_ingested',
            field=models.PositiveIntegerField(editable=False, default=0),
        ),
        migrations.AlterField(
            model_name='ingest',
            name='num_corpora_ingested',
            field=models.PositiveIntegerField(editable=False, default=0),
        ),
    ]
