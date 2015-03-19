# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('texts', '0004_auto_20150105_2226'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='text',
            name='text',
        ),
        migrations.AddField(
            model_name='text',
            name='text_ana',
            field=models.TextField(null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='text',
            name='text_dipl',
            field=models.TextField(null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='text',
            name='text_norm',
            field=models.TextField(null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='text',
            name='xml_paula',
            field=models.TextField(null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='text',
            name='xml_tei',
            field=models.TextField(null=True, blank=True),
            preserve_default=True,
        ),
    ]
