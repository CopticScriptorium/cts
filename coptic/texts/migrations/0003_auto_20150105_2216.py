# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('texts', '0002_auto_20150105_2205'),
    ]

    operations = [
        migrations.CreateModel(
            name='Author',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, verbose_name='ID', serialize=False)),
                ('name', models.CharField(max_length=200)),
                ('urn_code', models.CharField(max_length=200)),
                ('created', models.DateTimeField(verbose_name='Date of author creation')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='text',
            name='author',
            field=models.ForeignKey(default=0, blank=True, to='texts.Author'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='text',
            name='created',
            field=models.DateTimeField(default=datetime.date(2015, 1, 5), verbose_name='Date of text creation', editable=False),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='text',
            name='modified',
            field=models.DateTimeField(default=datetime.date(2015, 1, 5), verbose_name='Most recent date text was modified'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='text',
            name='collection',
            field=models.ForeignKey(to='texts.Collection', blank=True),
        ),
        migrations.AlterField(
            model_name='text',
            name='ingest',
            field=models.ForeignKey(to='texts.Ingest', blank=True),
        ),
    ]
