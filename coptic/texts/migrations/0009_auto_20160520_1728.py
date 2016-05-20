# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('texts', '0008_auto_20160504_2338'),
    ]

    operations = [
        migrations.AlterField(
            model_name='searchfieldvalue',
            name='title',
            field=models.CharField(max_length=500),
        ),
    ]
