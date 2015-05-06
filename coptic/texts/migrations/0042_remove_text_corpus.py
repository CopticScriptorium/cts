# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('texts', '0041_auto_20150505_2209'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='text',
            name='corpus',
        ),
    ]
