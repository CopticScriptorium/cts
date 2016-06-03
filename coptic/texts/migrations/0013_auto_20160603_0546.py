# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('texts', '0012_auto_20160603_0537'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='corpusmeta',
            name='corpus_name',
        ),
        migrations.RemoveField(
            model_name='textmeta',
            name='corpus_name',
        ),
    ]
