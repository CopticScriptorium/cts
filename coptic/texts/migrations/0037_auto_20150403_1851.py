# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('texts', '0036_collection_textgroup_urn_code'),
    ]

    operations = [
        migrations.AlterField(
            model_name='searchfield',
            name='splittable',
            field=models.CharField(null=True, blank=True, max_length=200),
        ),
    ]
