# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('topica', '0004_auto_20150918_1932'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='clusterlinkage',
            unique_together=set([]),
        ),
        migrations.RemoveField(
            model_name='clusterlinkage',
            name='from_cluster',
        ),
        migrations.RemoveField(
            model_name='clusterlinkage',
            name='to_cluster',
        ),
        migrations.RemoveField(
            model_name='cluster',
            name='cohesion',
        ),
        migrations.RemoveField(
            model_name='cluster',
            name='linkages',
        ),
        migrations.DeleteModel(
            name='ClusterLinkage',
        ),
    ]
