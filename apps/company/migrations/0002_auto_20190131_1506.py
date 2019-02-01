# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2019-01-31 15:06
from __future__ import unicode_literals

import apps.company.models
from django.conf import settings
import django.contrib.postgres.fields.citext
from django.db import migrations, models
import django.db.models.deletion
import partial_index


class Migration(migrations.Migration):

    dependencies = [
        ('company', '0001_initial'),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name='usercompany',
            name='company_use_user_id_ad6b21_partial',
        ),
        migrations.RemoveField(
            model_name='company',
            name='company_id',
        ),
        migrations.RemoveField(
            model_name='company',
            name='is_active',
        ),
        migrations.RemoveField(
            model_name='company',
            name='is_verified',
        ),
        migrations.RemoveField(
            model_name='usercompany',
            name='inactive_on',
        ),
        migrations.RemoveField(
            model_name='usercompany',
            name='join_on',
        ),
        migrations.AddField(
            model_name='company',
            name='city',
            field=models.CharField(blank=True, max_length=128),
        ),
        migrations.AddField(
            model_name='company',
            name='state',
            field=models.CharField(blank=True, max_length=128),
        ),
        migrations.AddField(
            model_name='company',
            name='status',
            field=models.PositiveIntegerField(
                choices=[(1, b'UNVERIFIED'), (2, b'ACTIVE'), (3, b'INACTIVE')], default=1),
        ),
        migrations.AddField(
            model_name='link',
            name='link_type',
            field=models.PositiveIntegerField(
                choices=[(1, b'TWITTER'), (2, b'FACEBOOK'), (3, b'GOOGLE')], default=1),
        ),
        migrations.AddField(
            model_name='usercompany',
            name='join_at',
            field=models.DateTimeField(default=None, null=True),
        ),
        migrations.AddField(
            model_name='usercompany',
            name='left_at',
            field=models.DateTimeField(default=None, null=True),
        ),
        migrations.AlterField(
            model_name='company',
            name='address',
            field=models.CharField(max_length=256),
        ),
        migrations.AlterField(
            model_name='company',
            name='logo',
            field=models.ImageField(
                upload_to=apps.company.models.company_logo_dir),
        ),
        migrations.AlterField(
            model_name='company',
            name='name',
            field=django.contrib.postgres.fields.citext.CICharField(
                max_length=256, unique=True),
        ),
        migrations.AlterField(
            model_name='usercompany',
            name='company',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,
                                    related_name='employees', to='company.Company'),
        ),
        migrations.AlterField(
            model_name='usercompany',
            name='designation',
            field=models.PositiveIntegerField(choices=[(
                1, b'HR'), (2, b'CEO'), (3, b'CTO'), (4, b'SDE_1'), (5, b'SDE_2')], default=4),
        ),
        migrations.AlterField(
            model_name='usercompany',
            name='status',
            field=models.PositiveIntegerField(
                choices=[(1, b'INVITED'), (2, b'ACTIVE'), (3, b'INACTIVE')], default=1),
        ),
        migrations.AlterField(
            model_name='usercompany',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,
                                    related_name='usercompany', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterUniqueTogether(
            name='link',
            unique_together=set([('company', 'link_type')]),
        ),
        migrations.AddIndex(
            model_name='usercompany',
            index=partial_index.PartialIndex(
                fields=['user', 'company'], name='company_use_user_id_099c95_partial', unique=True, where=partial_index.PQ(status__in=(1, 3))),
        ),
        migrations.RemoveField(
            model_name='link',
            name='name',
        ),
    ]
