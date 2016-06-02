# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('texts', '0010_auto_20160527_0547'),
    ]

    operations = [
        migrations.AlterField(
            model_name='corpus',
            name='github_paula',
            field=models.CharField(max_length=50, blank=True),
        ),
        migrations.AlterField(
            model_name='corpus',
            name='github_relannis',
            field=models.CharField(max_length=50, blank=True),
        ),
        migrations.AlterField(
            model_name='corpus',
            name='github_tei',
            field=models.CharField(max_length=50, blank=True),
        ),
    ]
