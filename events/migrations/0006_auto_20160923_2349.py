# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2016-09-23 23:49
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0005_campaign_sync_time'),
    ]

    operations = [
        migrations.AddField(
            model_name='campaign',
            name='email_opt_in',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='campaign',
            name='parent_id',
            field=models.CharField(default=2, max_length=255),
            preserve_default=False,
        ),
    ]
