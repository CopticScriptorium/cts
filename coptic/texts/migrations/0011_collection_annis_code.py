# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('texts', '0010_auto_20150122_1848'),
    ]

    operations = [
        migrations.AddField(
            model_name='collection',
            name='annis_code',
            field=models.CharField(default='', max_length=200),
            preserve_default=False,
        ),
    ]
