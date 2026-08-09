from unittest.mock import patch, MagicMock
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from apps.user.models import User, AgencyMemberList
from apps.scanner.models import (
    LinkRemovalRequestFromCustomer,
    LinkRemovalRequestFromAgencyMember,
    LinkRemovalVerification,
)
from apps.scanner.verification import verify_url_availability
from apps.scanner.tasks import verify_link_removal_task


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class LinkRemovalVerificationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.customer = User.objects.create_user(
            email="customer_test@example.com",
            password="Password123!",
            full_name="Test Customer",
            role="customer",
            term_and_condition_accepted=True
        )
        self.agency = User.objects.create_user(
            email="agency_test@example.com",
            password="Password123!",
            full_name="Test Agency",
            role="agency",
            term_and_condition_accepted=True
        )
        self.agency_member = AgencyMemberList.objects.create(
            agency=self.agency,
            name="Agency Member"
        )

    @patch("requests.get")
    def test_200_html_page_available(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.url = "https://example.com/page1"
        mock_resp.headers = {"Content-Type": "text/html; charset=utf-8"}
        mock_resp.history = []
        mock_get.return_value = mock_resp

        res = verify_url_availability("https://example.com/page1")
        self.assertEqual(res["verification_status"], "available")
        self.assertEqual(res["http_status_code"], 200)

    @patch("requests.head")
    def test_200_direct_image_available(self, mock_head):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.url = "https://cdn.example.com/photo.jpg"
        mock_resp.headers = {"Content-Type": "image/jpeg"}
        mock_resp.history = []
        mock_head.return_value = mock_resp

        res = verify_url_availability("https://cdn.example.com/photo.jpg")
        self.assertEqual(res["verification_status"], "available")
        self.assertEqual(res["http_status_code"], 200)

    @patch("requests.head")
    def test_200_direct_video_available(self, mock_head):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.url = "https://cdn.example.com/video.mp4"
        mock_resp.headers = {"Content-Type": "video/mp4"}
        mock_resp.history = []
        mock_head.return_value = mock_resp

        res = verify_url_availability("https://cdn.example.com/video.mp4")
        self.assertEqual(res["verification_status"], "available")
        self.assertEqual(res["http_status_code"], 200)

    @patch("requests.get")
    def test_404_not_found_removed(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_resp.url = "https://example.com/deleted-page"
        mock_resp.headers = {}
        mock_get.return_value = mock_resp

        req = LinkRemovalRequestFromCustomer.objects.create(
            customer=self.customer,
            link="https://example.com/deleted-page"
        )
        task_res = verify_link_removal_task(req.id, "customer", 0)

        req.refresh_from_db()
        self.assertEqual(req.status, "removed")
        self.assertEqual(task_res["status"], "removed")
        self.assertTrue(LinkRemovalVerification.objects.filter(customer_request=req, verification_status="removed").exists())

    @patch("requests.get")
    def test_410_gone_removed(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 410
        mock_resp.url = "https://example.com/gone-page"
        mock_resp.headers = {}
        mock_get.return_value = mock_resp

        req = LinkRemovalRequestFromCustomer.objects.create(
            customer=self.customer,
            link="https://example.com/gone-page"
        )
        task_res = verify_link_removal_task(req.id, "customer", 0)

        req.refresh_from_db()
        self.assertEqual(req.status, "removed")

    @patch("requests.get")
    def test_451_legal_unavailable_removed(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 451
        mock_resp.url = "https://example.com/legal-blocked"
        mock_resp.headers = {}
        mock_get.return_value = mock_resp

        req = LinkRemovalRequestFromCustomer.objects.create(
            customer=self.customer,
            link="https://example.com/legal-blocked"
        )
        verify_link_removal_task(req.id, "customer", 0)

        req.refresh_from_db()
        self.assertEqual(req.status, "removed")

    @patch("requests.get")
    def test_302_redirect_to_homepage_removed(self, mock_get):
        mock_history = [MagicMock(status_code=302)]
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.url = "https://example.com/"
        mock_resp.headers = {"Content-Type": "text/html"}
        mock_resp.history = mock_history
        mock_get.return_value = mock_resp

        req = LinkRemovalRequestFromCustomer.objects.create(
            customer=self.customer,
            link="https://example.com/john-doe/video123"
        )
        verify_link_removal_task(req.id, "customer", 0)

        req.refresh_from_db()
        self.assertEqual(req.status, "removed")

    @patch("requests.get")
    def test_302_redirect_to_valid_content_available(self, mock_get):
        mock_history = [MagicMock(status_code=302)]
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.url = "https://example.com/new-path/video123"
        mock_resp.headers = {"Content-Type": "text/html"}
        mock_resp.history = mock_history
        mock_get.return_value = mock_resp

        res = verify_url_availability("https://example.com/old-path/video123")
        self.assertEqual(res["verification_status"], "available")

    @patch("requests.get")
    def test_503_temporary_error_retry(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 503
        mock_resp.url = "https://example.com/temp-error"
        mock_resp.headers = {}
        mock_get.return_value = mock_resp

        req = LinkRemovalRequestFromCustomer.objects.create(
            customer=self.customer,
            link="https://example.com/temp-error"
        )
        task_res = verify_link_removal_task(req.id, "customer", 0)

        req.refresh_from_db()
        self.assertEqual(req.status, "pending")
        self.assertEqual(task_res["status"], "temporarily_unavailable")

    @patch("requests.get")
    def test_403_access_blocked(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 403
        mock_resp.url = "https://example.com/protected"
        mock_resp.headers = {}
        mock_get.return_value = mock_resp

        req = LinkRemovalRequestFromCustomer.objects.create(
            customer=self.customer,
            link="https://example.com/protected"
        )
        task_res = verify_link_removal_task(req.id, "customer", 0)

        req.refresh_from_db()
        self.assertEqual(req.status, "pending")
        self.assertEqual(task_res["status"], "blocked")

    @patch("requests.get")
    def test_already_removed_manual_override_protected(self, mock_get):
        req = LinkRemovalRequestFromCustomer.objects.create(
            customer=self.customer,
            link="https://example.com/manually-removed",
            status="removed"
        )

        task_res = verify_link_removal_task(req.id, "customer", 0)
        self.assertEqual(task_res["status"], "already_removed")
        mock_get.assert_not_called()

    @patch("requests.get")
    def test_dashboard_full_deleted_site_reflects_removed_links(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_resp.url = "https://example.com/deleted1"
        mock_resp.headers = {}
        mock_get.return_value = mock_resp

        req = LinkRemovalRequestFromCustomer.objects.create(
            customer=self.customer,
            link="https://example.com/deleted1"
        )
        verify_link_removal_task(req.id, "customer", 0)

        self.client.force_authenticate(user=self.customer)
        dashboard_url = reverse("user_dashboard_data")
        response = self.client.get(dashboard_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["number_of_full_deleted_site"], 1)
        self.assertEqual(response.data["data"]["number_of_delivered_site"], 1)
