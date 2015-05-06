# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('texts', '0043_text_corpus'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='corpus',
            name='textgroup_urn_code',
        ),
    ]
