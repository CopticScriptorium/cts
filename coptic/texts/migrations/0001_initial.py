# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Author',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', serialize=False, auto_created=True)),
                ('name', models.CharField(max_length=200)),
                ('urn_code', models.CharField(max_length=200)),
                ('created', models.DateTimeField(verbose_name='Date of author creation')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Collection',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', serialize=False, auto_created=True)),
                ('title', models.CharField(max_length=200)),
                ('urn_code', models.CharField(max_length=200)),
                ('created', models.DateTimeField(verbose_name='Date of collection creation')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Ingest',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', serialize=False, auto_created=True)),
                ('user', models.CharField(max_length=200)),
                ('date', models.DateTimeField(verbose_name='Date that the ingest occurred')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Text',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', serialize=False, auto_created=True)),
                ('title', models.CharField(max_length=200)),
                ('text', models.TextField()),
                ('author', models.ForeignKey(to='texts.Author')),
                ('collection', models.ForeignKey(to='texts.Collection')),
                ('ingest', models.ForeignKey(to='texts.Ingest')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
