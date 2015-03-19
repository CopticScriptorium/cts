# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('texts', '0020_auto_20150301_0131'),
    ]

    operations = [
        migrations.AddField(
            model_name='collection',
            name='annis_corpus_name',
            field=models.CharField(max_length=200, default=''),
            preserve_default=False,
        ),
    ]
