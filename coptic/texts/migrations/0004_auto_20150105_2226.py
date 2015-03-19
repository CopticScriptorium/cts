# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('texts', '0003_auto_20150105_2216'),
    ]

    operations = [
        migrations.AlterField(
            model_name='text',
            name='author',
            field=models.ForeignKey(to='texts.Author', blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='text',
            name='collection',
            field=models.ForeignKey(to='texts.Collection', blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='text',
            name='created',
            field=models.DateTimeField(verbose_name='Date of text creation', auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='text',
            name='ingest',
            field=models.ForeignKey(to='texts.Ingest', blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='text',
            name='modified',
            field=models.DateTimeField(verbose_name='Most recent date text was modified', auto_now=True),
        ),
        migrations.AlterField(
            model_name='text',
            name='text',
            field=models.TextField(null=True, blank=True),
        ),
    ]
