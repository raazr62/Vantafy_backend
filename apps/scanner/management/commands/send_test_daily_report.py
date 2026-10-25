from django.core.management.base import BaseCommand
from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone
from apps.utils.helpers import send_email
from apps.system_setting.models import AboutSystem


class Command(BaseCommand):
    help = "Send a test daily report email to the specified email address or preview HTML locally."

    def add_arguments(self, parser):
        parser.add_argument(
            "--email",
            type=str,
            default="sawafrafa003@gmail.com",
            help="Recipient email address (default: sawafrafa003@gmail.com)",
        )
        parser.add_argument(
            "--name",
            type=str,
            default="Sawaf Rafa",
            help="Subscriber display name",
        )
        parser.add_argument(
            "--new",
            type=int,
            default=14,
            help="Number of new links discovered",
        )
        parser.add_argument(
            "--deleted",
            type=int,
            default=9,
            help="Number of links successfully deleted",
        )
        parser.add_argument(
            "--save-html",
            action="store_true",
            help="Save rendered HTML to test_daily_report.html for local browser preview",
        )

    def handle(self, *args, **options):
        recipient_email = options["email"]
        recipient_name = options["name"]
        new_count = options["new"]
        deleted_count = options["deleted"]

        about_system = AboutSystem.objects.first()
        logo_url = (
            about_system.get_absolute_logo_url()
            if about_system
            else "https://midia-mixer.s3.us-east-2.amazonaws.com/system_setting/logo/1.png"
        )

        today_str = timezone.now().strftime("%b %d, %Y")

        context = {
            "user": {"full_name": recipient_name},
            "new_links_count": new_count,
            "deleted_links_count": deleted_count,
            "report_date": today_str,
            "dashboard_url": getattr(settings, "FRONTEND_URL", "https://Vantafy.com"),
            "system_info": about_system or {"name": "Vantafy", "email": "support@Vantafy.com"},
            "logo_url": logo_url,
        }

        html_message = render_to_string("email/daily_report_template.html", context)

        if options["save_html"]:
            import os
            save_path = os.path.join(settings.BASE_DIR, "templates", "email", "test_daily_report.html")
            with open(save_path, "w", encoding="utf-8") as f:
                f.write(html_message)
            self.stdout.write(self.style.SUCCESS(f"Saved rendered HTML to {save_path}"))

        subject = f"Your Daily Vantafy Scan & Removal Report ({today_str})"
        plain_body = (
            f"Hello {recipient_name},\n\n"
            f"Daily Summary:\n"
            f"New Links Discovered: {new_count}\n"
            f"Links Deleted: {deleted_count}\n\n"
            f"Visit your dashboard: {context['dashboard_url']}"
        )

        self.stdout.write(f"Sending test daily report to {recipient_email}...")
        try:
            send_email(
                subject=subject,
                body=plain_body,
                to_emails=[recipient_email],
                from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
                html_body=html_message,
            )
            self.stdout.write(self.style.SUCCESS(f"Email sent successfully to {recipient_email}! Check your inbox."))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Failed to send email: {e}"))
