from django.core.management.base import BaseCommand
from nb_hook.models import *
from datetime import datetime, timedelta

class Command(BaseCommand):
    def handle(self, *args, **options):
        print("Removing old logs more than 48 hours ago...")

        date_from = datetime.now() - timedelta(hours=12)
        print date_from
        Log.objects.filter(created_at__lte=date_from).delete()

        print("Done")

