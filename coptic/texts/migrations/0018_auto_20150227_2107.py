# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('texts', '0017_auto_20150227_1855'),
    ]

    operations = [
        migrations.CreateModel(
            name='SearchFieldValue',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, auto_created=True, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='searchfield',
            name='texts_field',
            field=models.CharField(default='', max_length=200),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='searchfield',
            name='values',
            field=models.ForeignKey(blank=True, to='texts.SearchFieldValue', null=True, editable=False),
            preserve_default=True,
        ),
    ]
