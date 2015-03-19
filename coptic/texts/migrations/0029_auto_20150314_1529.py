# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('texts', '0028_auto_20150309_1340'),
    ]

    operations = [
        migrations.CreateModel(
            name='HtmlVisualization',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID', auto_created=True)),
                ('slug', models.CharField(max_length=200)),
            ],
            options={
                'verbose_name': 'HTML Visualization',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='HtmlVisualizationFormat',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID', auto_created=True)),
                ('title', models.CharField(max_length=200)),
                ('slug', models.CharField(max_length=200)),
            ],
            options={
                'verbose_name': 'HTML Visualization Format',
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='htmlvisualization',
            name='visualization_format',
            field=models.ForeignKey(null=True, blank=True, to='texts.HtmlVisualizationFormat'),
            preserve_default=True,
        ),
        migrations.RemoveField(
            model_name='text',
            name='html_ana',
        ),
        migrations.RemoveField(
            model_name='text',
            name='html_dipl',
        ),
        migrations.RemoveField(
            model_name='text',
            name='html_norm',
        ),
        migrations.RemoveField(
            model_name='text',
            name='xml_paula',
        ),
        migrations.RemoveField(
            model_name='text',
            name='xml_tei',
        ),
        migrations.AddField(
            model_name='collection',
            name='html_visualization_formats',
            field=models.ManyToManyField(to='texts.HtmlVisualizationFormat', blank=True, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='text',
            name='html_visualizations',
            field=models.ManyToManyField(to='texts.HtmlVisualization', blank=True, null=True),
            preserve_default=True,
        ),
    ]
