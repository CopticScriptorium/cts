# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('texts', '0005_text_is_expired'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='searchfield',
            name='annis_name',
        ),
        migrations.RemoveField(
            model_name='searchfieldvalue',
            name='value',
        ),
    ]
