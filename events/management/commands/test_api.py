from django.core.management.base import BaseCommand
from events.sync import *
from django.conf import settings
from apis import sf_backends


class Command(BaseCommand):

    def handle(self, *args, **options):
        # if counter reaches the limit, abort and return
        if not sf_backends.check_count():
            return

        obj = dict(
            Email='walter@fissionstrategy.com',
            Email_Language__c='IT',
        )
        print sf_backends.insert_user(obj)