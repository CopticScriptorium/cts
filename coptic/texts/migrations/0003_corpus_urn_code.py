# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('texts', '0002_remove_corpus_urn_code'),
    ]

    operations = [
        migrations.AddField(
            model_name='corpus',
            name='urn_code',
            field=models.CharField(default='', max_length=200),
            preserve_default=False,
        ),
    ]
