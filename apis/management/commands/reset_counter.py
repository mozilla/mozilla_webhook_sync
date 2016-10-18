from django.core.management.base import BaseCommand
from apis import sf_backends


class Command(BaseCommand):
    def handle(self, *args, **options):
        print("Reset Counter")
        sf_backends.reset_counter()
