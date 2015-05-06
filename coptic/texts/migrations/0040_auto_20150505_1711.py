# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('texts', '0039_auto_20150505_1444'),
    ]

    operations = [
        migrations.CreateModel(
            name='Corpus',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, auto_created=True, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('textgroup_urn_code', models.CharField(max_length=200)),
                ('urn_code', models.CharField(max_length=200)),
                ('html_corpora_code', models.CharField(max_length=200)),
                ('slug', models.SlugField(max_length=40)),
                ('created', models.DateTimeField(editable=False)),
                ('modified', models.DateTimeField(editable=False)),
                ('annis_code', models.CharField(max_length=200)),
                ('annis_corpus_name', models.CharField(max_length=200)),
                ('github', models.CharField(max_length=200)),
                ('html_visualization_formats', models.ManyToManyField(blank=True, null=True, to='texts.HtmlVisualizationFormat')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.RemoveField(
            model_name='collection',
            name='html_visualization_formats',
        ),
        migrations.AlterField(
            model_name='text',
            name='collection',
            field=models.ForeignKey(blank=True, null=True, to='texts.Corpus'),
        ),
        migrations.DeleteModel(
            name='Collection',
        ),
    ]
