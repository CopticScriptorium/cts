# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('texts', '0018_auto_20150227_2107'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='searchfield',
            name='values',
        ),
        migrations.AddField(
            model_name='searchfieldvalue',
            name='field',
            field=models.ForeignKey(to='texts.SearchField', blank=True, editable=False, null=True),
            preserve_default=True,
        ),
    ]
