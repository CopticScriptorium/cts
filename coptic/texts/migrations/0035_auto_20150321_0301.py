# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('texts', '0034_auto_20150319_1817'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='searchfieldvalue',
            name='collections',
        ),
        migrations.AddField(
            model_name='searchfieldvalue',
            name='texts',
            field=models.ManyToManyField(to='texts.Text', null=True, blank=True),
            preserve_default=True,
        ),
    ]
