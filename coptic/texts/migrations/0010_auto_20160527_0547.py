# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('texts', '0009_auto_20160520_1728'),
    ]

    operations = [
        migrations.AddField(
            model_name='corpus',
            name='github_paula',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='corpus',
            name='github_relannis',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='corpus',
            name='github_tei',
            field=models.BooleanField(default=False),
        ),
    ]
