# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('texts', '0003_corpus_urn_code'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='corpus',
            name='html_corpora_code',
        ),
    ]
