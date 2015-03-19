# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('texts', '0011_collection_annis_code'),
    ]

    operations = [
        migrations.AddField(
            model_name='collection',
            name='github',
            field=models.CharField(max_length=200, default=''),
            preserve_default=False,
        ),
    ]
