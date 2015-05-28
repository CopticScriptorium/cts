# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('texts', '0004_remove_corpus_html_corpora_code'),
    ]

    operations = [
        migrations.AddField(
            model_name='text',
            name='is_expired',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
    ]
