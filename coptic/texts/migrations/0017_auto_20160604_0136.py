# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('texts', '0016_auto_20160604_0133'),
    ]

    operations = [
        migrations.AlterField(
            model_name='specialmeta',
            name='name',
            field=models.CharField(max_length=200, unique=True),
        ),
    ]
