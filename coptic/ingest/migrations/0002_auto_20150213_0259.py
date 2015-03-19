# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('ingest', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='ingest',
            name='created',
            field=models.DateTimeField(default=datetime.datetime(2015, 2, 13, 2, 59, 11, 478898), editable=False),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='ingest',
            name='modified',
            field=models.DateTimeField(default=datetime.datetime(2015, 2, 13, 2, 59, 19, 842668), editable=False),
            preserve_default=False,
        ),
    ]
