# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('annis', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='annisserver',
            old_name='base_url',
            new_name='base_domain',
        ),
        migrations.RenameField(
            model_name='annisserver',
            old_name='meta_url',
            new_name='corpus_metadata_url',
        ),
        migrations.RenameField(
            model_name='annisserver',
            old_name='html_url',
            new_name='html_visualization_url',
        ),
        migrations.AddField(
            model_name='annisserver',
            name='document_metadata_url',
            field=models.CharField(default='', max_length=200),
            preserve_default=False,
        ),
    ]
