# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime


class Migration(migrations.Migration):

    replaces = [('texts', '0001_initial'), ('texts', '0002_auto_20150105_2205'), ('texts', '0003_auto_20150105_2216'), ('texts', '0004_auto_20150105_2226'), ('texts', '0005_auto_20150105_2230'), ('texts', '0006_auto_20150105_2232'), ('texts', '0007_auto_20150105_2235'), ('texts', '0008_auto_20150105_2238'), ('texts', '0009_auto_20150105_2241'), ('texts', '0010_auto_20150122_1848'), ('texts', '0011_collection_annis_code'), ('texts', '0012_collection_github'), ('texts', '0013_auto_20150212_2134'), ('texts', '0014_text_ingest'), ('texts', '0015_collection_html_corpora_code'), ('texts', '0016_text_urn_code'), ('texts', '0017_auto_20150227_1855'), ('texts', '0018_auto_20150227_2107'), ('texts', '0019_auto_20150228_0043'), ('texts', '0020_auto_20150301_0131'), ('texts', '0021_collection_annis_corpus_name'), ('texts', '0022_docname'), ('texts', '0023_docname_collections'), ('texts', '0024_auto_20150309_0253'), ('texts', '0025_auto_20150309_1326'), ('texts', '0026_remove_searchfield_texts_field'), ('texts', '0027_searchfield_texts_field'), ('texts', '0028_auto_20150309_1340'), ('texts', '0029_auto_20150314_1529'), ('texts', '0030_htmlvisualization_html'), ('texts', '0031_remove_htmlvisualization_slug'), ('texts', '0032_searchfield_splittable'), ('texts', '0033_auto_20150319_0346'), ('texts', '0034_auto_20150319_1817'), ('texts', '0035_auto_20150321_0301'), ('texts', '0036_collection_textgroup_urn_code'), ('texts', '0037_auto_20150403_1851'), ('texts', '0038_remove_searchfield_texts_field'), ('texts', '0039_auto_20150505_1444'), ('texts', '0040_auto_20150505_1711'), ('texts', '0041_auto_20150505_2209'), ('texts', '0042_remove_text_corpus')]

    dependencies = [
        ('ingest', '__first__'),
    ]

    operations = [
        migrations.CreateModel(
            name='Collection',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('title', models.CharField(max_length=200)),
                ('urn_code', models.CharField(max_length=200)),
                ('created', models.DateTimeField(verbose_name='Date of collection creation')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Text',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('title', models.CharField(max_length=200)),
                ('collection', models.ForeignKey(null=True, blank=True, to='texts.Collection')),
                ('author', models.ForeignKey(null=True, blank=True, to='texts.Author')),
                ('created', models.DateTimeField(editable=False)),
                ('modified', models.DateTimeField(editable=False)),
                ('slug', models.SlugField(max_length=40, default='author')),
                ('ingest', models.ForeignKey(null=True, blank=True, to='ingest.Ingest')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='collection',
            name='modified',
            field=models.DateTimeField(default=datetime.date(2015, 1, 5), editable=False),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='collection',
            name='created',
            field=models.DateTimeField(editable=False),
        ),
        migrations.AddField(
            model_name='collection',
            name='slug',
            field=models.SlugField(max_length=40, default=''),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='collection',
            name='annis_code',
            field=models.CharField(max_length=200, default=''),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='collection',
            name='github',
            field=models.CharField(max_length=200, default=''),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='collection',
            name='html_corpora_code',
            field=models.CharField(max_length=200, default=''),
            preserve_default=False,
        ),
        migrations.CreateModel(
            name='SearchField',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('title', models.CharField(max_length=200)),
                ('texts_field', models.CharField(max_length=200, default='')),
                ('annis_name', models.CharField(max_length=200, default='')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='SearchFieldValue',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('title', models.CharField(max_length=200)),
                ('search_field', models.ForeignKey(null=True, blank=True, to='texts.SearchField')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='collection',
            name='annis_corpus_name',
            field=models.CharField(max_length=200, default=''),
            preserve_default=False,
        ),
        migrations.CreateModel(
            name='DocName',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('doc_name', models.CharField(max_length=200)),
                ('collections', models.ForeignKey(null=True, blank=True, to='texts.Collection')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='searchfieldvalue',
            name='collections',
            field=models.ManyToManyField(null=True, blank=True, to='texts.Collection'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='searchfieldvalue',
            name='value',
            field=models.CharField(max_length=200, default=''),
            preserve_default=False,
        ),
        migrations.AlterModelOptions(
            name='docname',
            options={'verbose_name': 'Document Name'},
        ),
        migrations.AlterModelOptions(
            name='searchfield',
            options={'verbose_name': 'Search Field'},
        ),
        migrations.AlterModelOptions(
            name='searchfieldvalue',
            options={'verbose_name': 'Search Field Value'},
        ),
        migrations.AddField(
            model_name='searchfield',
            name='order',
            field=models.IntegerField(default=1),
            preserve_default=False,
        ),
        migrations.RemoveField(
            model_name='searchfield',
            name='texts_field',
        ),
        migrations.CreateModel(
            name='HtmlVisualization',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
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
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
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
        migrations.AddField(
            model_name='text',
            name='html_visualizations',
            field=models.ManyToManyField(null=True, blank=True, to='texts.HtmlVisualization'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='htmlvisualization',
            name='html',
            field=models.TextField(default=''),
            preserve_default=False,
        ),
        migrations.RemoveField(
            model_name='htmlvisualization',
            name='slug',
        ),
        migrations.AddField(
            model_name='searchfield',
            name='splittable',
            field=models.CharField(max_length=200, blank=True, null=True),
            preserve_default=True,
        ),
        migrations.RemoveField(
            model_name='docname',
            name='collections',
        ),
        migrations.DeleteModel(
            name='DocName',
        ),
        migrations.CreateModel(
            name='TextMeta',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
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
        migrations.RemoveField(
            model_name='searchfieldvalue',
            name='collections',
        ),
        migrations.AddField(
            model_name='searchfieldvalue',
            name='texts',
            field=models.ManyToManyField(null=True, blank=True, to='texts.Text'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='collection',
            name='textgroup_urn_code',
            field=models.CharField(max_length=200, default=''),
            preserve_default=False,
        ),
        migrations.RemoveField(
            model_name='text',
            name='author',
        ),
        migrations.CreateModel(
            name='Corpus',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
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
                ('html_visualization_formats', models.ManyToManyField(null=True, blank=True, to='texts.HtmlVisualizationFormat')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.RenameField(
            model_name='text',
            old_name='collection',
            new_name='corpus',
        ),
        migrations.RemoveField(
            model_name='text',
            name='corpus',
        ),
        migrations.DeleteModel(
            name='Collection',
        ),
    ]
