# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('texts', '0032_searchfield_splittable'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='docname',
            name='collections',
        ),
        migrations.DeleteModel(
            name='DocName',
        ),
    ]
