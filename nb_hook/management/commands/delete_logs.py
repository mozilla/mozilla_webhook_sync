from django.core.management.base import BaseCommand
from nb_hook.models import *
from datetime import datetime, timedelta

class Command(BaseCommand):
    def handle(self, *args, **options):
        print("Removing old logs more than 48 hours ago...")

        date_from = datetime.now() - timedelta(days=2)
        old_logs = Log.objects.filter(created_at__lte=date_from)

        for log in old_logs:
            print log.created_at