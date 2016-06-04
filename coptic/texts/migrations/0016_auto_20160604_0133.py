# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('texts', '0015_specialmeta'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='specialmeta',
            options={'verbose_name': 'Special Metadata Name'},
        ),
        migrations.RemoveField(
            model_name='searchfield',
            name='order',
        ),
        migrations.RemoveField(
            model_name='searchfield',
            name='splittable',
        ),
    ]
