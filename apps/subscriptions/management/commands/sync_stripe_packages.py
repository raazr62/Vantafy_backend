from django.core.management.base import BaseCommand
from apps.subscriptions.models import Package
from apps.subscriptions.signals import create_or_sync_stripe_package


class Command(BaseCommand):
    help = "Syncs all database subscription packages with Stripe (creates/updates Stripe products and price IDs)."

    def handle(self, *args, **options):
        packages = Package.objects.all()
        count = packages.count()
        self.stdout.write(f"Starting Stripe sync for {count} packages...")

        for package in packages:
            self.stdout.write(f"Syncing package: '{package.name}' (ID: {package.pk})...")
            create_or_sync_stripe_package(package)

        self.stdout.write(self.style.SUCCESS(f"Successfully synced {count} packages with Stripe!"))
