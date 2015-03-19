# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ingest', '0002_auto_20150213_0259'),
    ]

    operations = [
        migrations.CreateModel(
            name='IngestSearchFields',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
                ('created', models.DateTimeField(editable=False)),
                ('modified', models.DateTimeField(editable=False)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
