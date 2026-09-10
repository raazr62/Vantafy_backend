from unittest.mock import patch
from django.test import TestCase, override_settings
from django.utils import timezone
from django.core.cache import cache
from apps.user.models import User, AgencyMemberList
from apps.subscriptions.models import Package, Subscription, Feature
from apps.scanner.models import CustomerScanProcessing, AgencyMemberScanProcessing
from apps.scanner.tasks import run_daily_subscription_scans, process_single_scan_job_task


@patch('apps.scanner.tasks.process_single_scan_job_task')
class ScheduledSubscriptionScanTests(TestCase):
    def setUp(self):
        cache.clear()
        # Create features
        self.daily_scan_feature = Feature.objects.create(name='Daily Scans')
        self.weekly_scan_feature = Feature.objects.create(name='Weekly Scans')

        # Create Packages
        self.starlet_pkg = Package.objects.create(
            name='Starlet',
            price=34.99,
            type=Package.PackageType.MONTHLY
        )
        self.starlet_pkg.features.add(self.weekly_scan_feature)

        self.superstar_pkg = Package.objects.create(
            name='Superstar',
            price=119.99,
            type=Package.PackageType.MONTHLY
        )
        self.superstar_pkg.features.add(self.daily_scan_feature)

        self.vip_pkg = Package.objects.create(
            name='VIP (Yearly)',
            price=1899.99,
            type=Package.PackageType.YEARLY
        )
        self.vip_pkg.features.add(self.daily_scan_feature)

        self.agency_pkg = Package.objects.create(
            name='Agency Starter',
            price=499.99,
            type=Package.PackageType.AGENCY
        )

        # Create Users
        self.customer_starlet = User.objects.create_user(
            email='starlet@example.com',
            password='Password123!',
            full_name='Starlet User',
            role='customer',
            term_and_condition_accepted=True
        )

        self.customer_superstar = User.objects.create_user(
            email='superstar@example.com',
            password='Password123!',
            full_name='Superstar User',
            role='customer',
            term_and_condition_accepted=True
        )

        self.customer_vip = User.objects.create_user(
            email='vip@example.com',
            password='Password123!',
            full_name='VIP User',
            role='customer',
            term_and_condition_accepted=True
        )

        self.agency_user = User.objects.create_user(
            email='agency@example.com',
            password='Password123!',
            full_name='Agency User',
            role='agency',
            term_and_condition_accepted=True
        )

        self.agency_member_1 = AgencyMemberList.objects.create(
            agency=self.agency_user,
            name="Agency Member 1"
        )
        self.agency_member_2 = AgencyMemberList.objects.create(
            agency=self.agency_user,
            name="Agency Member 2"
        )

        # Subscriptions
        Subscription.objects.create(
            user=self.customer_starlet,
            package=self.starlet_pkg,
            status='active',
            end_date=timezone.now() + timezone.timedelta(days=30)
        )

        Subscription.objects.create(
            user=self.customer_superstar,
            package=self.superstar_pkg,
            status='active',
            end_date=timezone.now() + timezone.timedelta(days=30)
        )

        Subscription.objects.create(
            user=self.customer_vip,
            package=self.vip_pkg,
            status='active',
            end_date=timezone.now() + timezone.timedelta(days=365)
        )

        Subscription.objects.create(
            user=self.agency_user,
            package=self.agency_pkg,
            status='active',
            end_date=timezone.now() + timezone.timedelta(days=30)
        )

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    def test_run_daily_subscription_scans_filters_eligible_packages(self, mock_sync):
        # Run orchestrator task
        res = run_daily_subscription_scans()

        self.assertEqual(res['status'], 'scheduled')
        # Expect 4 targets scheduled: Superstar user, VIP user, and 2 Agency Members
        self.assertEqual(res['total_scheduled'], 4)

        # Check CustomerScanProcessing created
        superstar_job = CustomerScanProcessing.objects.filter(customer=self.customer_superstar).first()
        self.assertIsNotNone(superstar_job)
        self.assertEqual(superstar_job.custom_search_name, 'Superstar User')

        vip_job = CustomerScanProcessing.objects.filter(customer=self.customer_vip).first()
        self.assertIsNotNone(vip_job)

        # Check Starlet user did NOT get a scan job
        starlet_job = CustomerScanProcessing.objects.filter(customer=self.customer_starlet).first()
        self.assertIsNone(starlet_job)

        # Check AgencyMemberScanProcessing created for agency members
        mem1_job = AgencyMemberScanProcessing.objects.filter(agency_member=self.agency_member_1).first()
        self.assertIsNotNone(mem1_job)

        mem2_job = AgencyMemberScanProcessing.objects.filter(agency_member=self.agency_member_2).first()
        self.assertIsNotNone(mem2_job)

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    def test_deduplication_skips_active_pending_running_jobs(self, mock_sync):
        # Pre-create an active scan job for Superstar user
        CustomerScanProcessing.objects.create(
            customer=self.customer_superstar,
            custom_search_name='Superstar User',
            status='running'
        )

        res = run_daily_subscription_scans()

        # Should schedule 3 targets instead of 4 (skipping superstar user)
        self.assertEqual(res['total_scheduled'], 3)
        self.assertEqual(CustomerScanProcessing.objects.filter(customer=self.customer_superstar).count(), 1)
