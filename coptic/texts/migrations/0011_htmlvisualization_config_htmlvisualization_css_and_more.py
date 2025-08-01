# Generated by Django 5.1.4 on 2025-01-19 16:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('texts', '0010_delete_metaorder_corpus_author'),
    ]

    operations = [
        migrations.AddField(
            model_name='htmlvisualization',
            name='config',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='htmlvisualization',
            name='css',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='text',
            name='content',
            field=models.TextField(default=''),
        ),
        migrations.AlterField(
            model_name='corpus',
            name='visualization_formats',
            field=models.TextField(db_index=True, default=''),
        ),
        migrations.AlterField(
            model_name='htmlvisualization',
            name='html',
            field=models.TextField(blank=True),
        ),
    ]
