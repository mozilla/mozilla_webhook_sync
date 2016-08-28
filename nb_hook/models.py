from __future__ import unicode_literals
from django.utils import timezone
from django.db import models


class TestHook(models.Model):
    created_at = models.DateTimeField(default=timezone.now)
    content = models.TextField(blank=True, null=True)
    
class ContactSync(models.Model):
    created_at = models.DateTimeField(default=timezone.now)
    contact = models.TextField(blank=True, null=True)
    synced = models.BooleanField(default=False)


class Campaign(models.Model):
    created_at = models.DateTimeField(default=timezone.now)
    nationbuilder_tag = models.CharField(max_length=255)
    salesforce_id = models.CharField(max_length=255)
