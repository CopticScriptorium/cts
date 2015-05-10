# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ingest', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Corpus',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, verbose_name='ID', primary_key=True)),
                ('created', models.DateTimeField(editable=False)),
                ('modified', models.DateTimeField(editable=False)),
                ('title', models.CharField(max_length=200)),
                ('slug', models.SlugField(max_length=40)),
                ('urn_code', models.CharField(max_length=200)),
                ('html_corpora_code', models.CharField(max_length=200)),
                ('annis_code', models.CharField(max_length=200)),
                ('annis_corpus_name', models.CharField(max_length=200)),
                ('github', models.CharField(max_length=200)),
            ],
            options={
                'verbose_name_plural': 'Corpora',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='CorpusMeta',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, verbose_name='ID', primary_key=True)),
                ('name', models.CharField(max_length=200)),
                ('value', models.CharField(max_length=200)),
                ('pre', models.CharField(max_length=200)),
                ('corpus_name', models.CharField(max_length=200)),
            ],
            options={
                'verbose_name': 'Corpus Meta Item',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='HtmlVisualization',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, verbose_name='ID', primary_key=True)),
                ('html', models.TextField()),
            ],
            options={
                'verbose_name': 'HTML Visualization',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='HtmlVisualizationFormat',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, verbose_name='ID', primary_key=True)),
                ('title', models.CharField(max_length=200)),
                ('button_title', models.CharField(max_length=200)),
                ('slug', models.CharField(max_length=200)),
            ],
            options={
                'verbose_name': 'HTML Visualization Format',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='SearchField',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, verbose_name='ID', primary_key=True)),
                ('title', models.CharField(max_length=200)),
                ('annis_name', models.CharField(max_length=200)),
                ('order', models.IntegerField()),
                ('splittable', models.CharField(null=True, blank=True, max_length=200)),
            ],
            options={
                'verbose_name': 'Search Field',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='SearchFieldValue',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, verbose_name='ID', primary_key=True)),
                ('title', models.CharField(max_length=200)),
                ('value', models.CharField(max_length=200)),
                ('search_field', models.ForeignKey(blank=True, to='texts.SearchField', null=True)),
            ],
            options={
                'verbose_name': 'Search Field Value',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Text',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, verbose_name='ID', primary_key=True)),
                ('title', models.CharField(max_length=200)),
                ('slug', models.SlugField(max_length=40)),
                ('created', models.DateTimeField(editable=False)),
                ('modified', models.DateTimeField(editable=False)),
                ('corpus', models.ForeignKey(blank=True, to='texts.Corpus', null=True)),
                ('html_visualizations', models.ManyToManyField(null=True, blank=True, to='texts.HtmlVisualization')),
                ('ingest', models.ForeignKey(blank=True, to='ingest.Ingest', null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='TextMeta',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, verbose_name='ID', primary_key=True)),
                ('name', models.CharField(max_length=200)),
                ('value', models.CharField(max_length=200)),
                ('pre', models.CharField(max_length=200)),
                ('corpus_name', models.CharField(max_length=200)),
            ],
            options={
                'verbose_name': 'Text Meta Item',
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='text',
            name='text_meta',
            field=models.ManyToManyField(null=True, blank=True, to='texts.TextMeta'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='searchfieldvalue',
            name='texts',
            field=models.ManyToManyField(null=True, blank=True, to='texts.Text'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='htmlvisualization',
            name='visualization_format',
            field=models.ForeignKey(blank=True, to='texts.HtmlVisualizationFormat', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='corpus',
            name='corpus_meta',
            field=models.ManyToManyField(null=True, blank=True, to='texts.CorpusMeta'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='corpus',
            name='html_visualization_formats',
            field=models.ManyToManyField(null=True, blank=True, to='texts.HtmlVisualizationFormat'),
            preserve_default=True,
        ),
    ]
