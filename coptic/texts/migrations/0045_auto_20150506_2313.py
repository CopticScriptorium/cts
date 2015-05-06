# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('texts', '0044_remove_corpus_textgroup_urn_code'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='corpus',
            options={'verbose_name_plural': 'Corpora'},
        ),
        migrations.AlterField(
            model_name='searchfield',
            name='annis_name',
            field=models.CharField(max_length=200),
        ),
        migrations.AlterField(
            model_name='text',
            name='slug',
            field=models.SlugField(max_length=40),
        ),
    ]
