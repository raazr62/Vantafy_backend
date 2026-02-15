from django.core.management.base import BaseCommand

from apps.cms.seed_data import seed_faq, seed_hero_radar_icon, seed_hero_section, seed_page, seed_represent_platform, seed_among_our_customers, seed_testimonials, seed_how_it_works, seed_identity_tracking
from apps.customer_support.seed_data import seed_messages
from apps.subscriptions.seed_data import seed_subscription_features, seed_subscription_packages, seed_subscription
from apps.system_setting.seed_data import seed_system_color, seed_system_setting, seed_social_media, seed_smtp_credentials
from apps.user.seed_users import seed_users, seed_customer_niches, seed_customer_stage_names
from apps.scanner.seed_data import seed_unauthorized_websites


class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        seed_users()
        seed_customer_niches()
        seed_customer_stage_names()
        seed_system_setting()
        seed_social_media()
        seed_smtp_credentials()
        seed_system_color()
        seed_page()
        seed_faq()
        seed_hero_section()
        seed_hero_radar_icon()
        seed_represent_platform()
        seed_among_our_customers()
        seed_testimonials()
        seed_how_it_works()
        seed_identity_tracking()
        seed_subscription_features()
        seed_subscription_packages()
        seed_subscription()
        seed_messages()
        seed_unauthorized_websites()
        
        
        
        
        self.stdout.write(self.style.SUCCESS("Seeding completed."))