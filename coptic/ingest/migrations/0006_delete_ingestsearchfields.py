# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ingest', '0005_auto_20150309_1326'),
    ]

    operations = [
        migrations.DeleteModel(
            name='IngestSearchFields',
        ),
    ]
