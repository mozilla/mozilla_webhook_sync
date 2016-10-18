from __future__ import unicode_literals
from django.utils import timezone
from django.db import models
from django.conf import settings


class Counter(models.Model):
    counter = models.IntegerField(default=0)
    last_updated = models.DateTimeField(default=timezone.now)
    counter_date = models.DateTimeField(default=timezone.now)