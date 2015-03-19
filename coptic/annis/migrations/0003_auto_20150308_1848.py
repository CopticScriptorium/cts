# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('annis', '0002_auto_20150308_1848'),
    ]

    operations = [
        migrations.RenameField(
            model_name='annisserver',
            old_name='api_url',
            new_name='meta_url',
        ),
    ]
