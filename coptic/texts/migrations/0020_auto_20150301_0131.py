# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('texts', '0019_auto_20150228_0043'),
    ]

    operations = [
        migrations.AddField(
            model_name='collection',
            name='author',
            field=models.ForeignKey(to='texts.Author', null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='searchfieldvalue',
            name='field',
            field=models.ForeignKey(to='texts.SearchField', null=True, blank=True),
        ),
    ]
