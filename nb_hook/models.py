from __future__ import unicode_literals
from django.utils import timezone
from django.db import models


class TestHook(models.Model):
    created_at = models.DateTimeField(default=timezone.now)
    content = models.TextField(blank=True, null=True)

