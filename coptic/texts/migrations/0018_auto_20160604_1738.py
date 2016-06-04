# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('texts', '0017_auto_20160604_0136'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='searchfieldvalue',
            name='search_field',
        ),
        migrations.RemoveField(
            model_name='searchfieldvalue',
            name='texts',
        ),
        migrations.DeleteModel(
            name='SearchField',
        ),
        migrations.DeleteModel(
            name='SearchFieldValue',
        ),
    ]
