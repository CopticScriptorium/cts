# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('texts', '0007_auto_20151123_0214'),
    ]

    operations = [
        migrations.AlterField(
            model_name='corpusmeta',
            name='value',
            field=models.CharField(max_length=500),
        ),
        migrations.AlterField(
            model_name='textmeta',
            name='value',
            field=models.CharField(max_length=500),
        ),
    ]
