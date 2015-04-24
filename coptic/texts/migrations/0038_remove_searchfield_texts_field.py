# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('texts', '0037_auto_20150403_1851'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='searchfield',
            name='texts_field',
        ),
    ]
