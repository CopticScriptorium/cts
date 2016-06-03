# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('texts', '0011_auto_20160602_0738'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='corpusmeta',
            name='pre',
        ),
        migrations.RemoveField(
            model_name='textmeta',
            name='pre',
        ),
    ]
