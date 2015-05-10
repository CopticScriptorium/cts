# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AnnisServer',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, verbose_name='ID', primary_key=True)),
                ('created', models.DateTimeField(editable=False)),
                ('modified', models.DateTimeField(editable=False)),
                ('title', models.CharField(max_length=200)),
                ('base_url', models.CharField(max_length=200)),
                ('meta_url', models.CharField(max_length=200)),
                ('html_url', models.CharField(max_length=200)),
            ],
            options={
                'verbose_name_plural': 'ANNIS Servers',
                'verbose_name': 'ANNIS Server',
            },
            bases=(models.Model,),
        ),
    ]
