# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('annis', '0003_annisserver_corpus_docname_url'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='annisserver',
            name='corpus_metadata_url',
        ),
    ]
