# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('texts', '0019_auto_20161212_2249'),
    ]

    operations = [
        migrations.CreateModel(
            name='MetaOrder',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, verbose_name='ID', auto_created=True)),
                ('name', models.CharField(unique=True, max_length=200)),
                ('order', models.IntegerField()),
            ],
            options={
                'verbose_name': 'Metadata Order',
            },
        ),
    ]
