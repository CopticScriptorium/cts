# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('texts', '0024_auto_20150309_0253'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='docname',
            options={'verbose_name': 'Document Name'},
        ),
        migrations.AlterModelOptions(
            name='searchfield',
            options={'verbose_name': 'Search Field'},
        ),
        migrations.AlterModelOptions(
            name='searchfieldvalue',
            options={'verbose_name': 'Search Field Value'},
        ),
        migrations.AddField(
            model_name='searchfield',
            name='order',
            field=models.IntegerField(default=1),
            preserve_default=False,
        ),
    ]
