# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ingest', '__first__'),
        ('texts', '0013_auto_20150212_2134'),
    ]

    operations = [
        migrations.AddField(
            model_name='text',
            name='ingest',
            field=models.ForeignKey(to='ingest.Ingest', null=True, blank=True),
            preserve_default=True,
        ),
    ]
