
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from apps.user.models import User, AgencyMemberList
from apps.scanner.models import CustomerScanProcessing, CustomerScanResult, AgencyMemberScanProcessing, AgencyMemberScanResult

class ScanRunTimeResultViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        # Create a customer user
        self.customer_user = User.objects.create_user(
            email='customer@example.com',
            password='password123',
            full_name='Customer User',
            role='customer',
            term_and_condition_accepted=True
        )
        
        # Create an agency user
        self.agency_user = User.objects.create_user(
            email='agency@example.com',
            password='password123',
            full_name='Agency User',
            role='agency',
            term_and_condition_accepted=True
        )
        # Create agency member
        self.agency_member = AgencyMemberList.objects.create(
            agency=self.agency_user,
            name="Test Member"
        )
        
        self.scan_url = reverse('scan_run_time_result')

    def test_get_scan_results_customer_no_job(self):
        self.client.force_authenticate(user=self.customer_user)
        response = self.client.get(self.scan_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['total_scanned'], 0)
        self.assertEqual(response.data['message'], 'No scan job found.')

    def test_get_scan_results_customer_with_job(self):
        # Create a scan job
        job = CustomerScanProcessing.objects.create(
            customer=self.customer_user,
            total_spiders=10,
            completed_spiders=5,
            status='running'
        )
        # Create some results
        result1 = CustomerScanResult.objects.create(
            customer=self.customer_user,
            scan_job=job,
            website='site1.com',
            status='pending'
        )
        result1.image_entries.create(image_url='http://site1.com/img1.jpg')
        
        result2 = CustomerScanResult.objects.create(
            customer=self.customer_user,
            scan_job=job,
            website='site2.com',
            status='reviewed'
        )
        
        self.client.force_authenticate(user=self.customer_user)
        response = self.client.get(self.scan_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['total_scanned'], 5)
        self.assertEqual(response.data['data']['total_matched'], 2)
        self.assertEqual(response.data['data']['total_image'], 1)
        self.assertEqual(response.data['data']['progress_percentage'], 50.0)
        self.assertEqual(response.data['data']['status'], 'running')
        self.assertEqual(len(response.data['data']['scan_results']), 2)

    def test_get_scan_results_agency_with_job(self):
        # Create a scan job for agency
        job = AgencyMemberScanProcessing.objects.create(
            agency=self.agency_user,
            agency_member=self.agency_member,
            total_spiders=20,
            completed_spiders=20,
            status='completed'
        )
        # Create a result
        result = AgencyMemberScanResult.objects.create(
            agency=self.agency_user,
            agency_member=self.agency_member,
            scan_job=job,
            website='site3.com'
        )
        
        self.client.force_authenticate(user=self.agency_user)
        response = self.client.get(self.scan_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['total_scanned'], 20)
        self.assertEqual(response.data['data']['total_matched'], 1)
        self.assertEqual(response.data['data']['progress_percentage'], 100.0)
        self.assertEqual(response.data['data']['status'], 'completed')
