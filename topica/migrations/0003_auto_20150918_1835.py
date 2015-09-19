# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('topica', '0002_cluster_cohesion'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cluster',
            name='cohesion',
            field=models.FloatField(default=1.0),
        ),
    ]
