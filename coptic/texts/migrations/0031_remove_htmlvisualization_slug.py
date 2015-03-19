# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('texts', '0030_htmlvisualization_html'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='htmlvisualization',
            name='slug',
        ),
    ]
