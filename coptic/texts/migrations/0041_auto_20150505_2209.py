# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('texts', '0040_auto_20150505_1711'),
    ]

    operations = [
        migrations.RenameField(
            model_name='text',
            old_name='collection',
            new_name='corpus',
        ),
    ]
