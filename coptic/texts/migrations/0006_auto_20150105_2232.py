# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('texts', '0005_auto_20150105_2230'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='text',
            name='text_ana',
        ),
        migrations.RemoveField(
            model_name='text',
            name='text_dipl',
        ),
        migrations.RemoveField(
            model_name='text',
            name='text_norm',
        ),
        migrations.AddField(
            model_name='text',
            name='html_ana',
            field=models.TextField(null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='text',
            name='html_dipl',
            field=models.TextField(null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='text',
            name='html_norm',
            field=models.TextField(null=True, blank=True),
            preserve_default=True,
        ),
    ]
