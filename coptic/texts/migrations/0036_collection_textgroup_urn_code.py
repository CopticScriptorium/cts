# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('texts', '0035_auto_20150321_0301'),
    ]

    operations = [
        migrations.AddField(
            model_name='collection',
            name='textgroup_urn_code',
            field=models.CharField(default='', max_length=200),
            preserve_default=False,
        ),
    ]
