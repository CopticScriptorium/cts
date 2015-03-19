# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('texts', '0022_docname'),
    ]

    operations = [
        migrations.AddField(
            model_name='docname',
            name='collections',
            field=models.ForeignKey(null=True, to='texts.Collection', blank=True),
            preserve_default=True,
        ),
    ]
