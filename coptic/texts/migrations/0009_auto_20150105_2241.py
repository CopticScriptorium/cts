# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('texts', '0008_auto_20150105_2238'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='ingest',
            name='date',
        ),
        migrations.AddField(
            model_name='ingest',
            name='created',
            field=models.DateTimeField(editable=False, default=datetime.date(2015, 1, 5)),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='ingest',
            name='modified',
            field=models.DateTimeField(editable=False, default=datetime.date(2015, 1, 5)),
            preserve_default=False,
        ),
    ]
