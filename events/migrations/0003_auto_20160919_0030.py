# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2016-09-19 00:30
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0002_campaignmember_member_nb_id'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='campaign',
            name='published_at',
        ),
        migrations.AddField(
            model_name='campaign',
            name='start_time',
            field=models.DateTimeField(blank=True, default=django.utils.timezone.now, null=True),
        ),
    ]
