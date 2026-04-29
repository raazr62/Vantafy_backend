from django.core.management.base import BaseCommand
from django.core.cache import cache

class Command(BaseCommand):
    help = 'Clear CMS cache'

    def handle(self, *args, **kwargs):
        cache.delete('landing_page_sections')
        self.stdout.write("✓ CMS cache cleared successfully")