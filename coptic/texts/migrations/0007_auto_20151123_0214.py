# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('texts', '0006_auto_20151102_0045'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='corpus',
            name='annis_code',
        ),
        migrations.AlterField(
            model_name='corpus',
            name='corpus_meta',
            field=models.ManyToManyField(to='texts.CorpusMeta', blank=True),
        ),
        migrations.AlterField(
            model_name='corpus',
            name='html_visualization_formats',
            field=models.ManyToManyField(to='texts.HtmlVisualizationFormat', blank=True),
        ),
        migrations.AlterField(
            model_name='searchfieldvalue',
            name='texts',
            field=models.ManyToManyField(to='texts.Text', blank=True),
        ),
        migrations.AlterField(
            model_name='text',
            name='html_visualizations',
            field=models.ManyToManyField(to='texts.HtmlVisualization', blank=True),
        ),
        migrations.AlterField(
            model_name='text',
            name='text_meta',
            field=models.ManyToManyField(to='texts.TextMeta', blank=True),
        ),
    ]
