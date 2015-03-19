# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('texts', '0029_auto_20150314_1529'),
    ]

    operations = [
        migrations.AddField(
            model_name='htmlvisualization',
            name='html',
            field=models.TextField(default=''),
            preserve_default=False,
        ),
    ]
