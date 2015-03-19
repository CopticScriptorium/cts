# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('texts', '0026_remove_searchfield_texts_field'),
    ]

    operations = [
        migrations.AddField(
            model_name='searchfield',
            name='texts_field',
            field=models.CharField(default='', max_length=200),
            preserve_default=False,
        ),
    ]
