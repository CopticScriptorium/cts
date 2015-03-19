# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('texts', '0023_docname_collections'),
    ]

    operations = [
        migrations.RenameField(
            model_name='searchfieldvalue',
            old_name='field',
            new_name='search_field',
        ),
        migrations.AddField(
            model_name='searchfield',
            name='annis_name',
            field=models.CharField(max_length=200, default=''),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='searchfieldvalue',
            name='collections',
            field=models.ManyToManyField(to='texts.Collection', blank=True, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='searchfieldvalue',
            name='value',
            field=models.CharField(max_length=200, default=''),
            preserve_default=False,
        ),
    ]
