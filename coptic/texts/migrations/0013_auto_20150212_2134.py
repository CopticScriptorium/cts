# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('texts', '0012_collection_github'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='text',
            name='ingest',
        ),
        migrations.DeleteModel(
            name='Ingest',
        ),
    ]
