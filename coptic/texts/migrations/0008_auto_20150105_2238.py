# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('texts', '0007_auto_20150105_2235'),
    ]

    operations = [
        migrations.AddField(
            model_name='author',
            name='modified',
            field=models.DateTimeField(default=datetime.date(2015, 1, 5), editable=False),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='collection',
            name='modified',
            field=models.DateTimeField(default=datetime.date(2015, 1, 5), editable=False),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='author',
            name='created',
            field=models.DateTimeField(editable=False),
        ),
        migrations.AlterField(
            model_name='collection',
            name='created',
            field=models.DateTimeField(editable=False),
        ),
        migrations.AlterField(
            model_name='text',
            name='created',
            field=models.DateTimeField(editable=False),
        ),
        migrations.AlterField(
            model_name='text',
            name='modified',
            field=models.DateTimeField(editable=False),
        ),
    ]
