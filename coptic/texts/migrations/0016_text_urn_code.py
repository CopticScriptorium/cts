# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('texts', '0015_collection_html_corpora_code'),
    ]

    operations = [
        migrations.AddField(
            model_name='text',
            name='urn_code',
            field=models.CharField(default='', max_length=200),
            preserve_default=False,
        ),
    ]
