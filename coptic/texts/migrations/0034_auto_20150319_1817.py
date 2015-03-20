# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('texts', '0033_auto_20150319_0346'),
    ]

    operations = [
        migrations.CreateModel(
            name='TextMeta',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=200)),
                ('value', models.CharField(max_length=200)),
                ('pre', models.CharField(max_length=200)),
                ('corpus_name', models.CharField(max_length=200)),
            ],
            options={
                'verbose_name': 'Text Meta Item',
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='text',
            name='text_meta',
            field=models.ManyToManyField(blank=True, to='texts.TextMeta', null=True),
            preserve_default=True,
        ),
    ]
