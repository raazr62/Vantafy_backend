import datetime
from unittest.mock import patch
from django.test import TestCase, override_settings
from django.utils import timezone
from django.core.cache import cache
from apps.user.models import User, AgencyMemberList
from apps.subscriptions.models import Package, Subscription, Feature
from apps.scanner.models import (
    CustomerScanProcessing,
    CustomerScanResult,
    CustomerScanResultPageUrl,
    LinkRemovalRequestFromCustomer,
)
from apps.scanner.tasks import (
    send_weekly_subscription_email_reports,
    send_daily_subscription_email_reports,
    run_weekly_subscription_scans,
)


@patch('apps.scanner.tasks.process_single_scan_job_task')
class WeeklyAndDailyReportTests(TestCase):
    def setUp(self):
        cache.clear()
        self.weekly_feature = Feature.objects.create(name='Weekly Scans')
        self.daily_feature = Feature.objects.create(name='Daily Scans')

        # Starlet Package
        self.starlet_pkg = Package.objects.create(
            name='Starlet',
            price=34.99,
            type=Package.PackageType.MONTHLY
        )
        self.starlet_pkg.features.add(self.weekly_feature)

        # Star Package
        self.star_pkg = Package.objects.create(
            name='Star',
            price=69.99,
            type=Package.PackageType.MONTHLY
        )
        self.star_pkg.features.add(self.weekly_feature)

        # Superstar Package (Daily)
        self.superstar_pkg = Package.objects.create(
            name='Superstar',
            price=119.99,
            type=Package.PackageType.MONTHLY
        )
        self.superstar_pkg.features.add(self.daily_feature)

        # Users
        self.starlet_user = User.objects.create_user(
            email='starlet_test@example.com',
            password='Password123!',
            full_name='Starlet Model',
            role='customer',
            term_and_condition_accepted=True
        )

        self.star_user = User.objects.create_user(
            email='star_test@example.com',
            password='Password123!',
            full_name='Star Model',
            role='customer',
            term_and_condition_accepted=True
        )

        self.superstar_user = User.objects.create_user(
            email='superstar_test@example.com',
            password='Password123!',
            full_name='Superstar Model',
            role='customer',
            term_and_condition_accepted=True
        )

        # Active Subscriptions
        Subscription.objects.create(
            user=self.starlet_user,
            package=self.starlet_pkg,
            status='active',
            end_date=timezone.now() + datetime.timedelta(days=30)
        )

        Subscription.objects.create(
            user=self.star_user,
            package=self.star_pkg,
            status='active',
            end_date=timezone.now() + datetime.timedelta(days=30)
        )

        Subscription.objects.create(
            user=self.superstar_user,
            package=self.superstar_pkg,
            status='active',
            end_date=timezone.now() + datetime.timedelta(days=30)
        )

    @patch('apps.scanner.tasks.send_email')
    def test_send_weekly_subscription_email_reports(self, mock_send_email, mock_process_task):
        # Create scan result and links discovered in past 7 days for starlet user
        scan_res = CustomerScanResult.objects.create(
            customer=self.starlet_user,
            website='example_spider'
        )
        CustomerScanResultPageUrl.objects.create(
            customer_scan_result=scan_res,
            page_url='https://example.com/leaked1.jpg'
        )
        CustomerScanResultPageUrl.objects.create(
            customer_scan_result=scan_res,
            page_url='https://example.com/leaked2.jpg'
        )

        # Create link removal request marked as 'removed' in past 7 days for starlet user
        LinkRemovalRequestFromCustomer.objects.create(
            customer=self.starlet_user,
            link='https://example.com/leaked1.jpg',
            status='removed'
        )

        # Run task
        res = send_weekly_subscription_email_reports()

        self.assertEqual(res['status'], 'completed')
        self.assertEqual(res['total_emails_sent'], 2)  # starlet_user & star_user

        # Verify mock_send_email calls
        recipients = [call.kwargs.get('to_emails')[0] for call in mock_send_email.call_args_list]
        self.assertIn('starlet_test@example.com', recipients)
        self.assertIn('star_test@example.com', recipients)
        self.assertNotIn('superstar_test@example.com', recipients)

    @patch('apps.scanner.tasks.send_email')
    def test_send_daily_subscription_email_reports(self, mock_send_email, mock_process_task):
        # Create scan result and links discovered in past 24h for superstar user
        scan_res = CustomerScanResult.objects.create(
            customer=self.superstar_user,
            website='example_spider'
        )
        CustomerScanResultPageUrl.objects.create(
            customer_scan_result=scan_res,
            page_url='https://example.com/leaked_daily.jpg'
        )

        # Create link removal request marked as 'removed' for superstar user
        LinkRemovalRequestFromCustomer.objects.create(
            customer=self.superstar_user,
            link='https://example.com/leaked_daily.jpg',
            status='removed'
        )

        # Run task
        res = send_daily_subscription_email_reports()

        self.assertEqual(res['status'], 'completed')
        self.assertEqual(res['total_emails_sent'], 1)  # superstar_user

        # Verify mock_send_email calls
        recipients = [call.kwargs.get('to_emails')[0] for call in mock_send_email.call_args_list]
        self.assertIn('superstar_test@example.com', recipients)
        self.assertNotIn('starlet_test@example.com', recipients)
        self.assertNotIn('star_test@example.com', recipients)

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    def test_run_weekly_subscription_scans(self, mock_process_task):
        res = run_weekly_subscription_scans()

        self.assertEqual(res['status'], 'scheduled')
        self.assertEqual(res['total_scheduled'], 2)  # starlet_user & star_user

        # Verify CustomerScanProcessing records created
        jobs = CustomerScanProcessing.objects.all()
        customers_queued = [j.customer for j in jobs]
        self.assertIn(self.starlet_user, customers_queued)
        self.assertIn(self.star_user, customers_queued)
        self.assertNotIn(self.superstar_user, customers_queued)

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    def test_weekly_scan_deduplication(self, mock_process_task):
        # Create an existing pending job for starlet_user
        CustomerScanProcessing.objects.create(
            customer=self.starlet_user,
            custom_search_name='Starlet Model',
            status='pending'
        )

        res = run_weekly_subscription_scans()
        # Should only schedule star_user since starlet_user has an active pending scan job
        self.assertEqual(res['total_scheduled'], 1)
