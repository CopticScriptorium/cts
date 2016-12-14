# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('texts', '0013_auto_20160603_0546'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='corpus',
            name='corpus_meta',
        ),
        migrations.DeleteModel(
            name='CorpusMeta',
        ),
    ]
