# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2016-10-18 17:40
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('apis', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='counter',
            name='counter_date',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
