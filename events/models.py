from __future__ import unicode_literals
from django.utils import timezone
from django.db import models

# Create your models here.


class Campaign(models.Model):
    created_at = models.DateTimeField(default=timezone.now)
    name = models.TextField()
    start_time = models.DateTimeField(default=timezone.now, blank=True, null=True)
    nb_id = models.IntegerField()
    sf_id = models.CharField(max_length=255, blank=True, null=True)
    type = models.CharField(max_length=255, default='Event')
    creator_sf_id = models.CharField(max_length=255, blank=True, null=True)
    content = models.TextField(blank=True, null=True)
    sync_time = models.DateTimeField(default=timezone.now, blank=True, null=True)


class CampaignMember(models.Model):
    created_at = models.DateTimeField(default=timezone.now)
    campaign_id = models.ForeignKey(Campaign)
    member_sf_id = models.CharField(max_length=100, blank=True, null=True)
    member_nb_id = models.IntegerField(blank=True, null=True)
    attended_before = models.BooleanField(default=False)
    campaign_language = models.CharField(max_length=2, default='EN')


class LastSync(models.Model):
    last_sync = models.DateTimeField(default=timezone.now)
