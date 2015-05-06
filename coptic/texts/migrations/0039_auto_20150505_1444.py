# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('texts', '0038_remove_searchfield_texts_field'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='collection',
            name='author',
        ),
        migrations.RemoveField(
            model_name='text',
            name='author',
        ),
        migrations.DeleteModel(
            name='Author',
        ),
    ]
