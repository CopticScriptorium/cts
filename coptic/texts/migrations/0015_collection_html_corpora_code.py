# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('texts', '0014_text_ingest'),
    ]

    operations = [
        migrations.AddField(
            model_name='collection',
            name='html_corpora_code',
            field=models.CharField(max_length=200, default=''),
            preserve_default=False,
        ),
    ]
