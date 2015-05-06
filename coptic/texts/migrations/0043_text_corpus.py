# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('texts', '0042_remove_text_corpus'),
    ]

    operations = [
        migrations.AddField(
            model_name='text',
            name='corpus',
            field=models.ForeignKey(blank=True, null=True, to='texts.Corpus'),
            preserve_default=True,
        ),
    ]
