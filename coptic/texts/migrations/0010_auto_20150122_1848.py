# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('texts', '0009_auto_20150105_2241'),
    ]

    operations = [
        migrations.AddField(
            model_name='author',
            name='slug',
            field=models.SlugField(default='', max_length=40),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='collection',
            name='slug',
            field=models.SlugField(default='', max_length=40),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='text',
            name='slug',
            field=models.SlugField(default='author', max_length=40),
            preserve_default=False,
        ),
    ]
