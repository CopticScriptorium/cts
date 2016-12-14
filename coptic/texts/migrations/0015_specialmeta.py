# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('texts', '0014_auto_20160603_2356'),
    ]

    operations = [
        migrations.CreateModel(
            name='SpecialMeta',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('name', models.CharField(max_length=200)),
                ('order', models.IntegerField()),
                ('splittable', models.BooleanField(default=False)),
            ],
            options={
                'verbose_name': 'Special Metadata Names',
            },
        ),
    ]
