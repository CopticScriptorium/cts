# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('texts', '0027_searchfield_texts_field'),
    ]

    operations = [
        migrations.AlterField(
            model_name='searchfield',
            name='texts_field',
            field=models.CharField(max_length=200, null=True, blank=True),
        ),
    ]
