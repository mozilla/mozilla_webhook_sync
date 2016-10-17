from django.core.management.base import BaseCommand
from events.sync import *
from django.conf import settings
from apis.sf_backends import check_count


class Command(BaseCommand):
    def handle(self, *args, **options):
        print("Check API upper limit")
        if not check_count():
            return

        print("Begin syncing")

        event_list = nb_backends.fetch_events().json()

        for event in event_list['results']:
            event_dj = fetch_save_event(event)
            if event_dj is not False:
                record_campaign_members(event['id'])

        campaigns = Campaign.objects.all()

        nb_list = []
        dj_list = []
        for event in event_list['results']:
            nb_list.append(event['id'])

        for campaign in campaigns:
            dj_list.append(campaign.nb_id)

        for dj_item_id in dj_list:
            if dj_item_id not in nb_list:
                remove_campaign(dj_item_id)

        print("Done Syncing")
