# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('annis', '0002_auto_20150510_1942'),
    ]

    operations = [
        migrations.AddField(
            model_name='annisserver',
            name='corpus_docname_url',
            field=models.CharField(default='', max_length=200),
            preserve_default=False,
        ),
    ]
