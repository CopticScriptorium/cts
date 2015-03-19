# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('texts', '0006_auto_20150105_2232'),
    ]

    operations = [
        migrations.AlterField(
            model_name='text',
            name='created',
            field=models.DateTimeField(verbose_name='Date of text creation', editable=False),
        ),
        migrations.AlterField(
            model_name='text',
            name='modified',
            field=models.DateTimeField(verbose_name='Most recent date text was modified', editable=False),
        ),
    ]
