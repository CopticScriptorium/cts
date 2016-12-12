# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('texts', '0018_auto_20160604_1738'),
    ]

    operations = [
        migrations.AlterField(
            model_name='textmeta',
            name='value',
            field=models.CharField(max_length=10000),
        ),
    ]
