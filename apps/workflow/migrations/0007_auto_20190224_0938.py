# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2019-02-24 09:38
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workflow', '0006_auto_20190224_0936'),
    ]

    operations = [
        migrations.AlterField(
            model_name='task',
            name='status',
            field=models.PositiveIntegerField(choices=[(1, b'UPCOMING'), (2, b'ONGOING'), (3, b'COMPLETE')], default=1),
        ),
    ]
