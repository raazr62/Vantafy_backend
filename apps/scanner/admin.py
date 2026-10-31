from django.contrib import admin, messages as django_messages
from django.urls import path
from django.shortcuts import render, redirect
from django.core.paginator import Paginator
from django.db.models import Subquery, OuterRef, IntegerField, Q, Count, Max
from django.db.models.functions import Coalesce
from unfold.admin import ModelAdmin, TabularInline
from unfold.decorators import action
from django.db.models import Count
from apps.user.models import User
from .services import run_all_spiders_async
from .models import (
    CustomerScanProcessing, 
    CustomerScanResult, 
    CustomerScanResultImage, 
    CustomerScanResultVideo, 
    CustomerScanResultPageUrl, 
    UnauthorizedWebsiteAndEmail,
    AgencyMemberScanProcessing, 
    AgencyMemberScanResult,
    AgencyMemberScanResultImage,
    AgencyMemberScanResultVideo,
    AgencyMemberScanResultPageUrl,
    LinkRemovalRequestFromCustomer,
    LinkRemovalRequestFromAgencyMember,
    LinkRemovalVerification,
    CustomerScanUserSummary,
    AgencyMemberScanUserSummary,
)
from .tasks import enqueue_verification_for_request

from django.utils.html import format_html


@admin.register(UnauthorizedWebsiteAndEmail)
class UnauthorizedWebsiteAndEmailAdmin(ModelAdmin):
    list_display = ('website', 'email')
    search_fields = ('website', 'email')


# -------------------------
# Customer Scan Processing
# -------------------------
@admin.register(CustomerScanProcessing)
class CustomerScanProcessingAdmin(ModelAdmin):
    list_select_related = ('customer',)
    list_per_page = 50
    list_display = ('id', 'scanned_name_display', 'customer', 'status', 'progress_percentage_display', 'total_images_display', 'total_videos_display', 'total_page_urls_display', 'created_at', 'updated_at', 'completed_at')
    list_filter = ('status', 'created_at', 'updated_at')
    list_display_links =('id', 'scanned_name_display', 'customer', 'status', 'progress_percentage_display', 'total_images_display', 'total_videos_display', 'total_page_urls_display', 'created_at', 'updated_at', 'completed_at')
    search_fields = ('customer__full_name', 'customer__email', 'custom_search_name', 'error_message')
    readonly_fields = ('created_at', 'updated_at', 'completed_at', 'progress_percentage_display', 'total_images_display', 'total_videos_display', 'total_page_urls_display', 'scanned_name_display')
    actions_list = ["start_new_scan_action"]

    @action(description="Start New Scan by Name", icon="play_circle")
    def start_new_scan_action(self, request):
        return redirect("admin:scanner_customerscanprocessing_scannow")

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "scan-now/",
                self.admin_site.admin_view(self.admin_scan_now_view),
                name="scanner_customerscanprocessing_scannow",
            ),
            path(
                "all-scans/",
                self.admin_site.admin_view(self.admin_all_scans_view),
                name="scanner_customerscanprocessing_allscans",
            ),
            path(
                "scan-detail/<str:target_type>/<int:target_id>/",
                self.admin_site.admin_view(self.admin_scan_detail_view),
                name="scanner_scan_detail",
            ),
        ]
        return custom_urls + urls

    def admin_scan_detail_view(self, request, target_type, target_id):
        from django.urls import reverse
        from apps.user.models import User, AgencyMemberList
        from django.core.paginator import Paginator
        from django.db.models import Q
        from .models import (
            CustomerScanProcessing,
            CustomerScanResult,
            CustomerScanResultPageUrl,
            CustomerScanResultImage,
            AgencyMemberScanProcessing,
            AgencyMemberScanResult,
            AgencyMemberScanResultPageUrl,
            AgencyMemberScanResultImage,
        )

        if request.method == "POST":
            action = request.POST.get("action")
            selected_ids = request.POST.getlist("selected_link_ids")
            selected_image_ids = request.POST.getlist("selected_image_ids")

            if action == "delete_links":
                if selected_ids:
                    c_deleted, _ = CustomerScanResultPageUrl.objects.filter(id__in=selected_ids).delete()
                    a_deleted, _ = AgencyMemberScanResultPageUrl.objects.filter(id__in=selected_ids).delete()
                    total_deleted = c_deleted + a_deleted
                    django_messages.success(request, f"Successfully deleted {total_deleted} selected link(s).")
                else:
                    django_messages.warning(request, "No links were selected for deletion.")
                return redirect(request.get_full_path())

            elif action == "delete_images":
                if selected_image_ids:
                    c_deleted, _ = CustomerScanResultImage.objects.filter(id__in=selected_image_ids).delete()
                    a_deleted, _ = AgencyMemberScanResultImage.objects.filter(id__in=selected_image_ids).delete()
                    total_deleted = c_deleted + a_deleted
                    django_messages.success(request, f"Successfully deleted {total_deleted} selected image(s).")
                else:
                    django_messages.warning(request, "No images were selected for deletion.")
                return redirect(request.get_full_path())

            elif action == "send_mail":
                if selected_ids:
                    from .tasks import enqueue_dmca_notice_for_request, enqueue_verification_for_request
                    from .models import LinkRemovalRequestFromCustomer, LinkRemovalRequestFromAgencyMember
                    from apps.subscriptions.models import Subscription

                    already_submitted_c = CustomerScanResultPageUrl.objects.filter(id__in=selected_ids, send_mail_status='submitted').count()
                    already_submitted_a = AgencyMemberScanResultPageUrl.objects.filter(id__in=selected_ids, send_mail_status='submitted').count()
                    skipped_count = already_submitted_c + already_submitted_a

                    c_purls = CustomerScanResultPageUrl.objects.filter(id__in=selected_ids).exclude(send_mail_status='submitted').select_related('customer_scan_result__customer')
                    a_purls = AgencyMemberScanResultPageUrl.objects.filter(id__in=selected_ids).exclude(send_mail_status='submitted').select_related('agency_member_scan_result__agency', 'agency_member_scan_result__agency_member')

                    if not c_purls.exists() and not a_purls.exists():
                        django_messages.warning(request, f"The selected link(s) have already been submitted ({skipped_count} link(s) skipped). No duplicate emails were sent.")
                        return redirect(request.get_full_path())

                    new_links_count = c_purls.count() + a_purls.count()

                    target_user = None
                    if target_type == "customer":
                        target_user = User.objects.filter(id=target_id).first()
                    elif target_type == "agency_member":
                        ag_mem = AgencyMemberList.objects.select_related('agency').filter(id=target_id).first()
                        target_user = ag_mem.agency if ag_mem else None
                    elif target_type == "customer_job":
                        c_job = CustomerScanProcessing.objects.select_related('customer').filter(id=target_id).first()
                        target_user = c_job.customer if c_job else None
                    elif target_type == "agency_job":
                        a_job = AgencyMemberScanProcessing.objects.select_related('agency').filter(id=target_id).first()
                        target_user = a_job.agency if a_job else None

                    if not target_user:
                        first_c = c_purls.first()
                        if first_c and first_c.customer_scan_result:
                            target_user = first_c.customer_scan_result.customer
                        else:
                            first_a = a_purls.first()
                            if first_a and first_a.agency_member_scan_result:
                                target_user = first_a.agency_member_scan_result.agency

                    sub = Subscription.objects.filter(user=target_user, status='active').first() if target_user else None
                    if sub:
                        allowed, current_submitted, limit = sub.can_submit_links(new_links_count)
                        if not allowed:
                            django_messages.error(
                                request,
                                f"Cannot submit links! The monthly link removal limit ({limit} links/month) for the user's active subscription package would be exceeded. Current submitted: {current_submitted}, Attempting to submit: {new_links_count}."
                            )
                            return redirect(request.get_full_path())

                    sent_count = 0
                    for p_url in c_purls:
                        cust = p_url.customer_scan_result.customer if p_url.customer_scan_result else None
                        req, _ = LinkRemovalRequestFromCustomer.objects.get_or_create(customer=cust, link=p_url.page_url)
                        req.links = 'submitted'
                        req.save(update_fields=['links', 'updated_at'])
                        enqueue_dmca_notice_for_request(req)
                        enqueue_verification_for_request(req)
                        p_url.send_mail_status = 'submitted'
                        p_url.save(update_fields=['send_mail_status'])
                        sent_count += 1

                    for p_url in a_purls:
                        agency = p_url.agency_member_scan_result.agency if p_url.agency_member_scan_result else None
                        member = p_url.agency_member_scan_result.agency_member if p_url.agency_member_scan_result else None
                        req, _ = LinkRemovalRequestFromAgencyMember.objects.get_or_create(agency=agency, agency_member=member, link=p_url.page_url)
                        req.links = 'submitted'
                        req.save(update_fields=['links', 'updated_at'])
                        enqueue_dmca_notice_for_request(req)
                        enqueue_verification_for_request(req)
                        p_url.send_mail_status = 'submitted'
                        p_url.save(update_fields=['send_mail_status'])
                        sent_count += 1

                    if sub and sent_count > 0:
                        sub.increment_submitted_links(sent_count)

                    if skipped_count > 0:
                        django_messages.success(request, f"Successfully sent mail for {sent_count} link(s). ({skipped_count} link(s) skipped because they were already submitted).")
                    else:
                        django_messages.success(request, f"Successfully sent mail for {sent_count} selected link(s). Status updated to Submitted.")
                else:
                    django_messages.warning(request, "No links were selected for sending emails.")
                return redirect(request.get_full_path())

            elif action == "send_all_pending":
                from .tasks import enqueue_dmca_notice_for_request, enqueue_verification_for_request
                from .models import LinkRemovalRequestFromCustomer, LinkRemovalRequestFromAgencyMember
                from apps.subscriptions.models import Subscription

                target_user = None
                if target_type == "customer":
                    c_purls = CustomerScanResultPageUrl.objects.filter(customer_scan_result__customer_id=target_id, send_mail_status='pending').select_related('customer_scan_result__customer')
                    a_purls = AgencyMemberScanResultPageUrl.objects.none()
                    target_user = User.objects.filter(id=target_id).first()
                elif target_type == "agency_member":
                    c_purls = CustomerScanResultPageUrl.objects.none()
                    a_purls = AgencyMemberScanResultPageUrl.objects.filter(agency_member_scan_result__agency_member_id=target_id, send_mail_status='pending').select_related('agency_member_scan_result__agency', 'agency_member_scan_result__agency_member')
                    ag_mem = AgencyMemberList.objects.select_related('agency').filter(id=target_id).first()
                    target_user = ag_mem.agency if ag_mem else None
                elif target_type == "customer_job":
                    c_purls = CustomerScanResultPageUrl.objects.filter(customer_scan_result__scan_job_id=target_id, send_mail_status='pending').select_related('customer_scan_result__customer')
                    a_purls = AgencyMemberScanResultPageUrl.objects.none()
                    c_job = CustomerScanProcessing.objects.select_related('customer').filter(id=target_id).first()
                    target_user = c_job.customer if c_job else None
                elif target_type == "agency_job":
                    c_purls = CustomerScanResultPageUrl.objects.none()
                    a_purls = AgencyMemberScanResultPageUrl.objects.filter(agency_member_scan_result__scan_job_id=target_id, send_mail_status='pending').select_related('agency_member_scan_result__agency', 'agency_member_scan_result__agency_member')
                    a_job = AgencyMemberScanProcessing.objects.select_related('agency').filter(id=target_id).first()
                    target_user = a_job.agency if a_job else None

                total_to_send = c_purls.count() + a_purls.count()
                if total_to_send == 0:
                    django_messages.info(request, "No pending links to send.")
                    return redirect(request.get_full_path())

                sub = Subscription.objects.filter(user=target_user, status='active').first() if target_user else None
                if sub:
                    allowed, current_submitted, limit = sub.can_submit_links(total_to_send)
                    if not allowed:
                        django_messages.error(
                            request,
                            f"Cannot submit links! The monthly link removal limit ({limit} links/month) for the user's active subscription package would be exceeded. Current submitted: {current_submitted}, Attempting to submit: {total_to_send}."
                        )
                        return redirect(request.get_full_path())

                sent_count = 0
                for p_url in c_purls:
                    cust = p_url.customer_scan_result.customer if p_url.customer_scan_result else None
                    req, _ = LinkRemovalRequestFromCustomer.objects.get_or_create(customer=cust, link=p_url.page_url)
                    req.links = 'submitted'
                    req.save(update_fields=['links', 'updated_at'])
                    enqueue_dmca_notice_for_request(req)
                    enqueue_verification_for_request(req)
                    p_url.send_mail_status = 'submitted'
                    p_url.save(update_fields=['send_mail_status'])
                    sent_count += 1

                for p_url in a_purls:
                    agency = p_url.agency_member_scan_result.agency if p_url.agency_member_scan_result else None
                    member = p_url.agency_member_scan_result.agency_member if p_url.agency_member_scan_result else None
                    req, _ = LinkRemovalRequestFromAgencyMember.objects.get_or_create(agency=agency, agency_member=member, link=p_url.page_url)
                    req.links = 'submitted'
                    req.save(update_fields=['links', 'updated_at'])
                    enqueue_dmca_notice_for_request(req)
                    enqueue_verification_for_request(req)
                    p_url.send_mail_status = 'submitted'
                    p_url.save(update_fields=['send_mail_status'])
                    sent_count += 1

                if sub and sent_count > 0:
                    sub.increment_submitted_links(sent_count)

                django_messages.success(request, f"Successfully processed and sent DMCA notices for all {sent_count} pending link(s).")
                return redirect(request.get_full_path())

            elif action == "add_manual_links":
                raw_links = request.POST.get("manual_links", "").strip()
                requested_status = request.POST.get("manual_link_status", "").strip().lower()

                if requested_status not in ["pending", "submitted"]:
                    django_messages.warning(request, "Please select a valid link status (Pending or Submitted) before saving links.")
                    return redirect(request.get_full_path())

                if not raw_links:
                    django_messages.warning(request, "Please enter at least one link.")
                    return redirect(request.get_full_path())

                from urllib.parse import urlparse
                lines = [line.strip().strip("[]() ") for line in raw_links.splitlines() if line.strip()]
                added_count = 0

                customer_user = None
                agency_user = None
                agency_member_obj = None
                job_obj = None

                if target_type == "customer":
                    customer_user = User.objects.filter(id=target_id).first()
                elif target_type == "agency_member":
                    agency_member_obj = AgencyMemberList.objects.select_related('agency').filter(id=target_id).first()
                    agency_user = agency_member_obj.agency if agency_member_obj else None
                elif target_type == "customer_job":
                    job_obj = CustomerScanProcessing.objects.select_related('customer').filter(id=target_id).first()
                    customer_user = job_obj.customer if job_obj else None
                elif target_type == "agency_job":
                    job_obj = AgencyMemberScanProcessing.objects.select_related('agency', 'agency_member').filter(id=target_id).first()
                    agency_user = job_obj.agency if job_obj else None
                    agency_member_obj = job_obj.agency_member if job_obj else None

                for link_url in lines:
                    formatted_url = link_url
                    if not (formatted_url.startswith("http://") or formatted_url.startswith("https://")):
                        formatted_url = "https://" + formatted_url

                    parsed = urlparse(formatted_url)
                    website_source = parsed.netloc or "manual-entry"

                    if target_type in ["customer", "customer_job"]:
                        if target_type == "customer":
                            scan_res = CustomerScanResult.objects.filter(customer=customer_user, website=website_source).first()
                            if not scan_res:
                                scan_res = CustomerScanResult.objects.create(
                                    customer=customer_user,
                                    website=website_source,
                                    status='action_taken'
                                )
                        else:
                            scan_res = CustomerScanResult.objects.filter(scan_job=job_obj, website=website_source).first()
                            if not scan_res:
                                scan_res = CustomerScanResult.objects.create(
                                    customer=customer_user,
                                    scan_job=job_obj,
                                    website=website_source,
                                    status='action_taken'
                                )

                        p_url, created = CustomerScanResultPageUrl.objects.get_or_create(
                            customer_scan_result=scan_res,
                            page_url=formatted_url,
                            defaults={'send_mail_status': requested_status}
                        )
                        if created:
                            added_count += 1
                        elif p_url.send_mail_status != requested_status:
                            p_url.send_mail_status = requested_status
                            p_url.save(update_fields=['send_mail_status'])
                            added_count += 1

                    elif target_type in ["agency_member", "agency_job"]:
                        if target_type == "agency_member":
                            scan_res = AgencyMemberScanResult.objects.filter(agency=agency_user, agency_member=agency_member_obj, website=website_source).first()
                            if not scan_res:
                                scan_res = AgencyMemberScanResult.objects.create(
                                    agency=agency_user,
                                    agency_member=agency_member_obj,
                                    website=website_source,
                                    status='action_taken'
                                )
                        else:
                            scan_res = AgencyMemberScanResult.objects.filter(scan_job=job_obj, website=website_source).first()
                            if not scan_res:
                                scan_res = AgencyMemberScanResult.objects.create(
                                    agency=agency_user,
                                    agency_member=agency_member_obj,
                                    scan_job=job_obj,
                                    website=website_source,
                                    status='action_taken'
                                )

                        p_url, created = AgencyMemberScanResultPageUrl.objects.get_or_create(
                            agency_member_scan_result=scan_res,
                            page_url=formatted_url,
                            defaults={'send_mail_status': requested_status}
                        )
                        if created:
                            added_count += 1
                        elif p_url.send_mail_status != requested_status:
                            p_url.send_mail_status = requested_status
                            p_url.save(update_fields=['send_mail_status'])
                            added_count += 1

                if added_count > 0:
                    status_display = "Pending" if requested_status == "pending" else "Submitted"
                    django_messages.success(request, f"Successfully processed {added_count} link(s) with status '{status_display}'.")
                else:
                    django_messages.info(request, "No links were updated or added.")
                return redirect(request.get_full_path())

            elif action == "add_manual_images":
                uploaded_files = request.FILES.getlist("manual_image_files")
                raw_images = request.POST.get("manual_images", "").strip()
                custom_site = request.POST.get("website_source", "").strip()

                if not uploaded_files and not raw_images:
                    django_messages.warning(request, "Please select image file(s) to upload or enter image URLs.")
                    return redirect(request.get_full_path())

                from urllib.parse import urlparse
                added_count = 0

                customer_user = None
                agency_user = None
                agency_member_obj = None
                job_obj = None

                if target_type == "customer":
                    customer_user = User.objects.filter(id=target_id).first()
                elif target_type == "agency_member":
                    agency_member_obj = AgencyMemberList.objects.select_related('agency').filter(id=target_id).first()
                    agency_user = agency_member_obj.agency if agency_member_obj else None
                elif target_type == "customer_job":
                    job_obj = CustomerScanProcessing.objects.select_related('customer').filter(id=target_id).first()
                    customer_user = job_obj.customer if job_obj else None
                elif target_type == "agency_job":
                    job_obj = AgencyMemberScanProcessing.objects.select_related('agency', 'agency_member').filter(id=target_id).first()
                    agency_user = job_obj.agency if job_obj else None
                    agency_member_obj = job_obj.agency_member if job_obj else None

                if uploaded_files:
                    site_source = custom_site or "manual-upload"
                    if target_type in ["customer", "customer_job"]:
                        if target_type == "customer":
                            scan_res = CustomerScanResult.objects.filter(customer=customer_user, website=site_source).first()
                            if not scan_res:
                                scan_res = CustomerScanResult.objects.create(
                                    customer=customer_user,
                                    website=site_source,
                                    status='action_taken'
                                )
                        else:
                            scan_res = CustomerScanResult.objects.filter(scan_job=job_obj, website=site_source).first()
                            if not scan_res:
                                scan_res = CustomerScanResult.objects.create(
                                    customer=customer_user,
                                    scan_job=job_obj,
                                    website=site_source,
                                    status='action_taken'
                                )

                        for f_obj in uploaded_files:
                            fname = f_obj.name
                            img_obj = CustomerScanResultImage(
                                customer_scan_result=scan_res,
                                image_url=f"/media/customer_scan_images/{fname}"
                            )
                            img_obj.image.save(fname, f_obj, save=True)
                            scan_res.add_page_url(img_obj.image_url)
                            added_count += 1

                    elif target_type in ["agency_member", "agency_job"]:
                        if target_type == "agency_member":
                            scan_res = AgencyMemberScanResult.objects.filter(agency=agency_user, agency_member=agency_member_obj, website=site_source).first()
                            if not scan_res:
                                scan_res = AgencyMemberScanResult.objects.create(
                                    agency=agency_user,
                                    agency_member=agency_member_obj,
                                    website=site_source,
                                    status='action_taken'
                                )
                        else:
                            scan_res = AgencyMemberScanResult.objects.filter(scan_job=job_obj, website=site_source).first()
                            if not scan_res:
                                scan_res = AgencyMemberScanResult.objects.create(
                                    agency=agency_user,
                                    agency_member=agency_member_obj,
                                    scan_job=job_obj,
                                    website=site_source,
                                    status='action_taken'
                                )

                        for f_obj in uploaded_files:
                            fname = f_obj.name
                            img_obj = AgencyMemberScanResultImage(
                                agency_member_scan_result=scan_res,
                                image_url=f"/media/agency_member_scan_images/{fname}"
                            )
                            img_obj.image.save(fname, f_obj, save=True)
                            scan_res.add_page_url(img_obj.image_url)
                            added_count += 1

                if raw_images:
                    lines = [line.strip().strip("[]() ") for line in raw_images.splitlines() if line.strip()]
                    for img_url in lines:
                        formatted_url = img_url
                        if not (formatted_url.startswith("http://") or formatted_url.startswith("https://")):
                            formatted_url = "https://" + formatted_url

                        parsed = urlparse(formatted_url)
                        website_source = custom_site or (parsed.netloc or "manual-entry")

                        if target_type in ["customer", "customer_job"]:
                            if target_type == "customer":
                                scan_res = CustomerScanResult.objects.filter(customer=customer_user, website=website_source).first()
                                if not scan_res:
                                    scan_res = CustomerScanResult.objects.create(
                                        customer=customer_user,
                                        website=website_source,
                                        status='action_taken'
                                    )
                            else:
                                scan_res = CustomerScanResult.objects.filter(scan_job=job_obj, website=website_source).first()
                                if not scan_res:
                                    scan_res = CustomerScanResult.objects.create(
                                        customer=customer_user,
                                        scan_job=job_obj,
                                        website=website_source,
                                        status='action_taken'
                                    )

                            _, created = CustomerScanResultImage.objects.get_or_create(
                                customer_scan_result=scan_res,
                                image_url=formatted_url
                            )
                            scan_res.add_page_url(formatted_url)
                            if created:
                                added_count += 1

                        elif target_type in ["agency_member", "agency_job"]:
                            if target_type == "agency_member":
                                scan_res = AgencyMemberScanResult.objects.filter(agency=agency_user, agency_member=agency_member_obj, website=website_source).first()
                                if not scan_res:
                                    scan_res = AgencyMemberScanResult.objects.create(
                                        agency=agency_user,
                                        agency_member=agency_member_obj,
                                        website=website_source,
                                        status='action_taken'
                                    )
                            else:
                                scan_res = AgencyMemberScanResult.objects.filter(scan_job=job_obj, website=website_source).first()
                                if not scan_res:
                                    scan_res = AgencyMemberScanResult.objects.create(
                                        agency=agency_user,
                                        agency_member=agency_member_obj,
                                        scan_job=job_obj,
                                        website=website_source,
                                        status='action_taken'
                                    )

                            _, created = AgencyMemberScanResultImage.objects.get_or_create(
                                agency_member_scan_result=scan_res,
                                image_url=formatted_url
                            )
                            scan_res.add_page_url(formatted_url)
                            if created:
                                added_count += 1

                if added_count > 0:
                    django_messages.success(request, f"Successfully uploaded/added {added_count} image(s).")
                else:
                    django_messages.info(request, "No new unique images were added (the images may already exist).")
                return redirect(request.get_full_path())

        # GET request handling with server-side pagination & filtering
        link_page = request.GET.get('link_page', 1)
        link_q = request.GET.get('link_q', '').strip()
        link_status = request.GET.get('link_status', 'all').strip().lower()
        image_page = request.GET.get('image_page', 1)
        image_q = request.GET.get('image_q', '').strip()

        target_title = "Scan Details"
        target_subtitle = ""
        scan_type = "Individual"

        if target_type == "customer":
            customer = User.objects.filter(id=target_id).first()
            if not customer:
                django_messages.error(request, "Customer not found.")
                return redirect("admin:scanner_customerscanprocessing_allscans")
            target_title = customer.full_name or customer.email
            target_subtitle = f"Customer Scan Overview for {customer.email}"
            scan_type = "Individual Customer"
            results_qs = CustomerScanResult.objects.filter(customer=customer)
            all_links_qs = CustomerScanResultPageUrl.objects.filter(customer_scan_result__customer=customer).select_related('customer_scan_result')
            all_images_qs = CustomerScanResultImage.objects.filter(customer_scan_result__customer=customer).select_related('customer_scan_result')

        elif target_type == "agency_member":
            member = AgencyMemberList.objects.select_related('agency').filter(id=target_id).first()
            if not member:
                django_messages.error(request, "Agency member not found.")
                return redirect("admin:scanner_customerscanprocessing_allscans")
            target_title = member.name
            agency_email = member.agency.email if member.agency else ""
            target_subtitle = f"Agency Member Scan Overview ({agency_email})"
            scan_type = "Agency Member"
            results_qs = AgencyMemberScanResult.objects.filter(agency_member=member)
            all_links_qs = AgencyMemberScanResultPageUrl.objects.filter(agency_member_scan_result__agency_member=member).select_related('agency_member_scan_result')
            all_images_qs = AgencyMemberScanResultImage.objects.filter(agency_member_scan_result__agency_member=member).select_related('agency_member_scan_result')

        elif target_type == "customer_job":
            job = CustomerScanProcessing.objects.select_related('customer').filter(id=target_id).first()
            if not job:
                django_messages.error(request, "Customer scan run not found.")
                return redirect("admin:scanner_customerscanprocessing_allscans")
            target_title = job.search_name
            c_email = job.customer.email if job.customer else "-"
            target_subtitle = f"Individual Scan Run #{job.id} for {c_email}"
            scan_type = "Individual Execution"
            results_qs = job.results.all()
            all_links_qs = CustomerScanResultPageUrl.objects.filter(customer_scan_result__scan_job=job).select_related('customer_scan_result')
            all_images_qs = CustomerScanResultImage.objects.filter(customer_scan_result__scan_job=job).select_related('customer_scan_result')

        elif target_type == "agency_job":
            job = AgencyMemberScanProcessing.objects.select_related('agency', 'agency_member').filter(id=target_id).first()
            if not job:
                django_messages.error(request, "Agency scan run not found.")
                return redirect("admin:scanner_customerscanprocessing_allscans")
            target_title = job.search_name
            a_email = job.agency.email if job.agency else "-"
            target_subtitle = f"Agency Scan Run #{job.id} for {a_email}"
            scan_type = "Agency Execution"
            results_qs = job.results.all()
            all_links_qs = AgencyMemberScanResultPageUrl.objects.filter(agency_member_scan_result__scan_job=job).select_related('agency_member_scan_result')
            all_images_qs = AgencyMemberScanResultImage.objects.filter(agency_member_scan_result__scan_job=job).select_related('agency_member_scan_result')

        # Fast overall totals
        total_links_count = all_links_qs.count()
        total_pending_links_count = all_links_qs.filter(send_mail_status='pending').count()
        total_submitted_links_count = all_links_qs.filter(send_mail_status='submitted').count()
        total_images_count = all_images_qs.count()
        total_scan_results_count = results_qs.count()

        # Filter & Paginate Links (50 per page)
        filtered_links = all_links_qs
        if link_status in ['pending', 'submitted']:
            filtered_links = filtered_links.filter(send_mail_status=link_status)
        if link_q:
            if "customer" in target_type:
                filtered_links = filtered_links.filter(
                    Q(page_url__icontains=link_q) | Q(customer_scan_result__website__icontains=link_q)
                )
            else:
                filtered_links = filtered_links.filter(
                    Q(page_url__icontains=link_q) | Q(agency_member_scan_result__website__icontains=link_q)
                )

        links_paginator = Paginator(filtered_links.order_by('-id'), 50)
        page_urls_page = links_paginator.get_page(link_page)

        page_urls = []
        for p_url in page_urls_page:
            parent = p_url.customer_scan_result if "customer" in target_type else p_url.agency_member_scan_result
            page_urls.append({
                'id': p_url.id,
                'page_url': p_url.page_url,
                'website': parent.website if parent else '',
                'send_mail_status': getattr(p_url, 'send_mail_status', 'pending'),
                'send_mail_status_display': p_url.get_send_mail_status_display() if hasattr(p_url, 'get_send_mail_status_display') else 'Pending',
                'created_at': getattr(p_url, 'created_at', None),
            })

        # Filter & Paginate Images (36 per page)
        filtered_images = all_images_qs
        if image_q:
            if "customer" in target_type:
                filtered_images = filtered_images.filter(
                    Q(image_url__icontains=image_q) | Q(customer_scan_result__website__icontains=image_q)
                )
            else:
                filtered_images = filtered_images.filter(
                    Q(image_url__icontains=image_q) | Q(agency_member_scan_result__website__icontains=image_q)
                )

        images_paginator = Paginator(filtered_images.order_by('-id'), 36)
        images_page_obj = images_paginator.get_page(image_page)

        images = []
        for img in images_page_obj:
            parent = img.customer_scan_result if "customer" in target_type else img.agency_member_scan_result
            disp_url = img.image_url
            if not disp_url and img.image and img.image.name:
                try:
                    disp_url = img.image.url
                except Exception:
                    disp_url = ''
            images.append({
                'id': img.id,
                'image_url': img.image_url,
                'display_url': disp_url or img.image_url,
                'website': parent.website if parent else '',
            })

        # Scan results website summaries
        scan_results = []
        for res in results_qs.order_by('-created_at'):
            change_url_name = 'admin:scanner_customerscanresult_change' if "customer" in target_type else 'admin:scanner_agencymemberscanresult_change'
            c_url = reverse(change_url_name, args=[res.id])
            scan_results.append({
                'website': res.website,
                'status': res.status,
                'get_status_display': res.get_status_display(),
                'profile_url': res.profile_url,
                'contact_emails': res.contact_emails or [],
                'total_images': res.total_images,
                'total_videos': res.total_videos,
                'total_page_urls': res.total_page_urls,
                'created_at': res.created_at,
                'change_url': c_url,
            })

        context = {
            **self.admin_site.each_context(request),
            "title": f"Scan Details - {target_title}",
            "target_title": target_title,
            "target_subtitle": target_subtitle,
            "scan_type": scan_type,
            "page_urls": page_urls,
            "page_urls_page": page_urls_page,
            "total_links_count": total_links_count,
            "total_pending_links_count": total_pending_links_count,
            "total_submitted_links_count": total_submitted_links_count,
            "images": images,
            "images_page_obj": images_page_obj,
            "total_images_count": total_images_count,
            "scan_results": scan_results,
            "total_scan_results_count": total_scan_results_count,
            "link_q": link_q,
            "link_status": link_status,
            "image_q": image_q,
            "opts": self.model._meta,
        }
        return render(request, "admin/scanner/scan_detail.html", context)

    def admin_all_scans_view(self, request):
        from django.urls import reverse
        from datetime import datetime
        from django.db.models import Count, Q, Max
        from apps.user.models import User, AgencyMemberList
        from django.utils import timezone
        from apps.subscriptions.models import Subscription
        from django.core.paginator import Paginator

        search_query = request.GET.get('q', '').strip()
        status_filter = request.GET.get('status', '').strip().lower()
        view_mode = request.GET.get('view_mode', 'active').strip()
        page_number = request.GET.get('page', 1)

        if view_mode not in ['active', 'expired']:
            view_mode = 'active'

        active_subs = Subscription.objects.filter(status='active').select_related('package')
        user_sub_map = {sub.user_id: sub for sub in active_subs}

        def get_removals_info(u_id):
            if not u_id:
                return "-"
            sub = user_sub_map.get(u_id)
            if sub and sub.package:
                limit = sub.package.link_removal_limit_per_month
                submitted = sub.submitted_links
                if limit > 0:
                    left = max(0, limit - submitted)
                    return f"{left} / {limit}"
                return "Unlimited"
            return "No Active Plan"

        from apps.scanner.models import (
            CustomerScanProcessing,
            CustomerScanResult,
            CustomerScanResultPageUrl,
            AgencyMemberScanProcessing,
            AgencyMemberScanResult,
            AgencyMemberScanResultPageUrl,
        )

        # Fast indexed aggregate lookups to prevent Cartesian explosion on PostgreSQL
        c_scans = {
            r['customer_id']: r
            for r in CustomerScanProcessing.objects.values('customer_id').annotate(
                total_scans=Count('id'),
                last_scan_time=Max('completed_at')
            )
        }
        c_results = {
            r['customer_id']: r['last_result_time']
            for r in CustomerScanResult.objects.values('customer_id').annotate(
                last_result_time=Max('created_at')
            )
        }
        c_pending = {
            r['customer_scan_result__customer_id']: r['total']
            for r in CustomerScanResultPageUrl.objects.filter(send_mail_status='pending').values('customer_scan_result__customer_id').annotate(
                total=Count('id')
            )
        }

        # Agency member aggregates
        a_scans = {
            r['agency_member_id']: r
            for r in AgencyMemberScanProcessing.objects.values('agency_member_id').annotate(
                total_scans=Count('id'),
                last_scan_time=Max('completed_at')
            )
        }
        a_results = {
            r['agency_member_id']: r['last_result_time']
            for r in AgencyMemberScanResult.objects.values('agency_member_id').annotate(
                last_result_time=Max('created_at')
            )
        }
        a_pending = {
            r['agency_member_scan_result__agency_member_id']: r['total']
            for r in AgencyMemberScanResultPageUrl.objects.filter(send_mail_status='pending').values('agency_member_scan_result__agency_member_id').annotate(
                total=Count('id')
            )
        }

        # Fetch all Individual Customer Users
        customer_users = User.objects.filter(role='customer').only('id', 'email', 'full_name', 'created_at')

        # Fetch all Agency Member Users
        agency_members = AgencyMemberList.objects.select_related('agency').only('id', 'name', 'agency__id', 'agency__email')

        active_users = []
        expired_users = []

        for u in customer_users:
            c_name = u.full_name or u.email
            c_email = u.email
            scan_stat = c_scans.get(u.id, {})
            last_scan_time = scan_stat.get('last_scan_time')
            last_result_time = c_results.get(u.id)
            last_time = last_scan_time or last_result_time or u.created_at
            detail_url = reverse('admin:scanner_scan_detail', kwargs={'target_type': 'customer', 'target_id': u.id})

            pending_count = c_pending.get(u.id, 0)
            status_raw = 'pending' if pending_count > 0 else 'completed'
            status_display = 'Pending' if pending_count > 0 else 'Completed'

            is_active_sub = u.id in user_sub_map

            item_data = {
                'target_type': 'customer',
                'target_id': u.id,
                'customer_name': c_name,
                'customer_email': c_email,
                'scan_type': 'Individual',
                'total_scans': scan_stat.get('total_scans', 0),
                'last_scan_time': last_time,
                'status': status_display,
                'status_raw': status_raw,
                'total_pending_urls': pending_count,
                'removals_left': get_removals_info(u.id),
                'detail_url': detail_url,
                'is_active_sub': is_active_sub,
            }

            if is_active_sub:
                active_users.append(item_data)
            else:
                expired_users.append(item_data)

        for m in agency_members:
            m_name = m.name or (m.agency.email if m.agency else f"Agency Member #{m.id}")
            c_email = m.agency.email if m.agency else "-"
            scan_stat = a_scans.get(m.id, {})
            last_scan_time = scan_stat.get('last_scan_time')
            last_result_time = a_results.get(m.id)
            last_time = last_scan_time or last_result_time
            detail_url = reverse('admin:scanner_scan_detail', kwargs={'target_type': 'agency_member', 'target_id': m.id})

            pending_count = a_pending.get(m.id, 0)
            status_raw = 'pending' if pending_count > 0 else 'completed'
            status_display = 'Pending' if pending_count > 0 else 'Completed'

            is_active_sub = m.agency_id in user_sub_map if m.agency_id else False

            item_data = {
                'target_type': 'agency_member',
                'target_id': m.id,
                'customer_name': m_name,
                'customer_email': c_email,
                'scan_type': 'Agency',
                'total_scans': scan_stat.get('total_scans', 0),
                'last_scan_time': last_time,
                'status': status_display,
                'status_raw': status_raw,
                'total_pending_urls': pending_count,
                'removals_left': get_removals_info(m.agency_id),
                'detail_url': detail_url,
                'is_active_sub': is_active_sub,
            }

            if is_active_sub:
                active_users.append(item_data)
            else:
                expired_users.append(item_data)

        if search_query:
            q_lower = search_query.lower()
            active_users = [
                u for u in active_users
                if q_lower in u['customer_name'].lower() or q_lower in u['customer_email'].lower()
            ]
            expired_users = [
                u for u in expired_users
                if q_lower in u['customer_name'].lower() or q_lower in u['customer_email'].lower()
            ]

        if status_filter in ['pending', 'completed']:
            active_users = [u for u in active_users if u['status_raw'] == status_filter]
            expired_users = [u for u in expired_users if u['status_raw'] == status_filter]

        min_datetime = timezone.make_aware(datetime.min)
        active_users.sort(key=lambda x: x['last_scan_time'] if x['last_scan_time'] else min_datetime, reverse=True)
        expired_users.sort(key=lambda x: x['last_scan_time'] if x['last_scan_time'] else min_datetime, reverse=True)

        user_list = active_users if view_mode == 'active' else expired_users
        paginator = Paginator(user_list, 25)
        page_obj = paginator.get_page(page_number)

        context = {
            **self.admin_site.each_context(request),
            "title": "All Scans Overview",
            "active_users": active_users,
            "expired_users": expired_users,
            "active_users_count": len(active_users),
            "expired_users_count": len(expired_users),
            "displayed_scans": page_obj,
            "page_obj": page_obj,
            "view_mode": view_mode,
            "search_query": search_query,
            "status_filter": status_filter,
            "opts": self.model._meta,
        }
        return render(request, "admin/scanner/all_scans.html", context)


    def admin_scan_now_view(self, request):
        if request.method == "POST":
            name_to_scan = request.POST.get("name", "").strip()
            customer_id = request.POST.get("customer_id")

            if not name_to_scan:
                django_messages.error(request, "Please enter a name to scan.")
                return redirect("admin:scanner_customerscanprocessing_scannow")

            target_user = None
            if customer_id:
                try:
                    target_user = User.objects.get(id=customer_id)
                except User.DoesNotExist:
                    pass

            scan_job = CustomerScanProcessing.objects.create(
                customer=target_user,
                custom_search_name=name_to_scan
            )

            run_all_spiders_async(
                name_query=name_to_scan,
                job_id=scan_job.id,
                app_label="scanner",
                model_name="CustomerScanProcessing"
            )

            django_messages.success(
                request,
                f"Scan initiated successfully for name '{name_to_scan}' (Scan Job ID: {scan_job.id})."
            )
            return redirect("admin:scanner_customerscanprocessing_changelist")

        customers = User.objects.all().order_by("email")
        context = {
            **self.admin_site.each_context(request),
            "title": "Start New Scan by Name",
            "customers": customers,
            "opts": self.model._meta,
        }
        return render(request, "admin/scanner/scan_now.html", context)

    @admin.display(description='Scanned Name')
    def scanned_name_display(self, obj):
        return obj.search_name

    # Display methods for readonly fields
    @admin.display(description='Progress %')
    def progress_percentage_display(self, obj):
        return obj.progress_percentage

    @admin.display(description='Total Images')
    def total_images_display(self, obj):
        return obj.total_images

    @admin.display(description='Total Videos')
    def total_videos_display(self, obj):
        return obj.total_videos

    @admin.display(description='Total Page URLs')
    def total_page_urls_display(self, obj):
        return obj.total_page_urls


# -------------------------
# Customer Scan Result
# -------------------------
@admin.register(CustomerScanResult)
class CustomerScanResultAdmin(ModelAdmin):
    list_select_related = ('customer', 'scan_job')
    list_per_page = 50
    list_display = ('id', 'customer', 'website', 'status', 'total_images_display', 'total_videos_display', 'total_page_urls_display', 'created_at', 'updated_at')
    list_filter = ('status', 'website', 'created_at', 'updated_at')
    list_display_links =('id', 'customer', 'website', 'status', 'total_images_display', 'total_videos_display', 'total_page_urls_display', 'created_at', 'updated_at')
    search_fields = ('customer__full_name', 'customer__email', 'website')
    readonly_fields = ('created_at', 'updated_at', 'total_images_display', 'total_videos_display', 'total_page_urls_display')

    # Display methods to show related totals
    @admin.display(description='Total Images')
    def total_images_display(self, obj):
        return obj.total_images

    @admin.display(description='Total Videos')
    def total_videos_display(self, obj):
        return obj.total_videos

    @admin.display(description='Total Page URLs')
    def total_page_urls_display(self, obj):
        return obj.total_page_urls


class CustomerScanResultInline(TabularInline):
    per_page = 20
    model = CustomerScanResult
    fk_name = 'customer'
    extra = 0
    show_change_link = True
    fields = ('website', 'status', 'total_images_display', 'total_videos_display', 'total_page_urls_display', 'created_at')
    readonly_fields = ('status', 'total_images_display', 'total_videos_display', 'total_page_urls_display', 'created_at')

    @admin.display(description='Total Images')
    def total_images_display(self, obj):
        return obj.total_images if obj else 0

    @admin.display(description='Total Videos')
    def total_videos_display(self, obj):
        return obj.total_videos if obj else 0

    @admin.display(description='Total Page URLs')
    def total_page_urls_display(self, obj):
        return obj.total_page_urls if obj else 0


@admin.register(CustomerScanUserSummary)
class CustomerScanUserSummaryAdmin(ModelAdmin):
    list_display = ('email', 'full_name', 'total_websites_display', 'total_images_display', 'total_videos_display', 'total_page_urls_display', 'last_scanned_at_display')
    list_display_links = ('email', 'full_name')
    search_fields = ('email', 'full_name')
    readonly_fields = ('email', 'full_name', 'total_websites_display', 'total_images_display', 'total_videos_display', 'total_page_urls_display')
    inlines = [CustomerScanResultInline]
    list_per_page = 50

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        img_sq = CustomerScanResultImage.objects.filter(customer_scan_result__customer_id=OuterRef('pk')).values('customer_scan_result__customer_id').annotate(c=Count('id')).values('c')[:1]
        vid_sq = CustomerScanResultVideo.objects.filter(customer_scan_result__customer_id=OuterRef('pk')).values('customer_scan_result__customer_id').annotate(c=Count('id')).values('c')[:1]
        url_sq = CustomerScanResultPageUrl.objects.filter(customer_scan_result__customer_id=OuterRef('pk')).values('customer_scan_result__customer_id').annotate(c=Count('id')).values('c')[:1]
        web_sq = CustomerScanResult.objects.filter(customer_id=OuterRef('pk')).values('customer_id').annotate(c=Count('id')).values('c')[:1]
        last_sq = CustomerScanResult.objects.filter(customer_id=OuterRef('pk')).order_by('-created_at').values('created_at')[:1]
        return qs.filter(customer_scan_results__isnull=False).distinct().annotate(
            annotated_total_websites=Coalesce(Subquery(web_sq, output_field=IntegerField()), 0),
            annotated_total_images=Coalesce(Subquery(img_sq, output_field=IntegerField()), 0),
            annotated_total_videos=Coalesce(Subquery(vid_sq, output_field=IntegerField()), 0),
            annotated_total_page_urls=Coalesce(Subquery(url_sq, output_field=IntegerField()), 0),
            annotated_last_scanned_at=Subquery(last_sq),
        )

    @admin.display(description='Total Websites Scanned')
    def total_websites_display(self, obj):
        if hasattr(obj, 'annotated_total_websites'):
            return obj.annotated_total_websites
        return obj.customer_scan_results.count()

    @admin.display(description='Total Images')
    def total_images_display(self, obj):
        if hasattr(obj, 'annotated_total_images'):
            return obj.annotated_total_images
        return sum(res.total_images for res in obj.customer_scan_results.all())

    @admin.display(description='Total Videos')
    def total_videos_display(self, obj):
        if hasattr(obj, 'annotated_total_videos'):
            return obj.annotated_total_videos
        return sum(res.total_videos for res in obj.customer_scan_results.all())

    @admin.display(description='Total Page URLs')
    def total_page_urls_display(self, obj):
        if hasattr(obj, 'annotated_total_page_urls'):
            return obj.annotated_total_page_urls
        return sum(res.total_page_urls for res in obj.customer_scan_results.all())

    @admin.display(description='Latest Scan')
    def last_scanned_at_display(self, obj):
        if hasattr(obj, 'annotated_last_scanned_at') and obj.annotated_last_scanned_at:
            return obj.annotated_last_scanned_at
        latest = obj.customer_scan_results.order_by('-created_at').first()
        return latest.created_at if latest else "-"



# -------------------------
# Inlines for Scan Result Images/Videos/URLs
# -------------------------
class CustomerScanResultImageInline(TabularInline):
    per_page = 20
    model = CustomerScanResultImage
    extra = 0
    readonly_fields = ('image_preview', 'image')
    fields = ('image_preview', 'image_url', 'image')

    @admin.display(description='Preview')
    def image_preview(self, obj):
        if not obj:
            return "No Image"
        url = obj.image.url if obj.image else obj.image_url
        if url:
            return format_html(
                '<img src="{}" style="max-width: 150px; max-height: 150px; object-fit: contain; border-radius: 4px;" />',
                url,
            )
        return "No Image"

class CustomerScanResultVideoInline(TabularInline):
    per_page = 20
    model = CustomerScanResultVideo
    extra = 0

class CustomerScanResultPageUrlInline(TabularInline):
    per_page = 20
    model = CustomerScanResultPageUrl
    extra = 0

CustomerScanResultAdmin.inlines = [
    CustomerScanResultImageInline,
    CustomerScanResultVideoInline,
    CustomerScanResultPageUrlInline
]

@admin.register(CustomerScanResultImage)
class CustomerScanResultImageAdmin(ModelAdmin):
    list_select_related = ('customer_scan_result', 'customer_scan_result__customer')
    list_per_page = 50
    list_display = ('id', 'customer_scan_result', 'image_preview', 'image_url')
    search_fields = ('image_url', 'customer_scan_result__website', 'customer_scan_result__customer__email')
    readonly_fields = ('image_preview',)

    @admin.display(description='Preview')
    def image_preview(self, obj):
        if not obj:
            return "No Image"
        url = obj.image.url if obj.image else obj.image_url
        if url:
            return format_html(
                '<img src="{}" style="max-width: 150px; max-height: 150px; object-fit: contain; border-radius: 4px;" />',
                url,
            )
        return "No Image"

# -------------------------
# Agency Scan Processing
# -------------------------
@admin.register(AgencyMemberScanProcessing)
class AgencyMemberScanProcessingAdmin(ModelAdmin):
    list_select_related = ('agency', 'agency_member')
    list_per_page = 50
    list_display = ('id', 'scanned_name_display', 'agency', 'agency_member', 'status', 'progress_percentage_display', 'total_images_display', 'total_videos_display', 'total_page_urls_display', 'created_at', 'updated_at', 'completed_at')
    list_filter = ('status', 'created_at', 'updated_at')
    list_display_links = ('id', 'scanned_name_display', 'agency', 'agency_member', 'status', 'progress_percentage_display', 'total_images_display', 'total_videos_display', 'total_page_urls_display', 'created_at', 'updated_at', 'completed_at')
    search_fields = ('agency__full_name', 'agency__email', 'agency_member__name', 'custom_search_name', 'error_message')
    readonly_fields = ('created_at', 'updated_at', 'completed_at', 'progress_percentage_display', 'total_images_display', 'total_videos_display', 'total_page_urls_display', 'scanned_name_display')

    @admin.display(description='Scanned Name')
    def scanned_name_display(self, obj):
        return obj.search_name

    @admin.display(description='Progress %')
    def progress_percentage_display(self, obj):
        return obj.progress_percentage

    @admin.display(description='Total Images')
    def total_images_display(self, obj):
        return obj.total_images

    @admin.display(description='Total Videos')
    def total_videos_display(self, obj):
        return obj.total_videos

    @admin.display(description='Total Page URLs')
    def total_page_urls_display(self, obj):
        return obj.total_page_urls

# -------------------------
# Agency Scan Result
# -------------------------
@admin.register(AgencyMemberScanResult)
class AgencyMemberScanResultAdmin(ModelAdmin):
    list_select_related = ('agency', 'agency_member', 'scan_job')
    list_per_page = 50
    list_display = ('id', 'agency', 'agency_member', 'website', 'status', 'total_images_display', 'total_videos_display', 'total_page_urls_display', 'created_at', 'updated_at')
    list_filter = ('status', 'website', 'created_at', 'updated_at')
    list_display_links = ('id', 'agency', 'agency_member', 'website', 'status', 'total_images_display', 'total_videos_display', 'total_page_urls_display', 'created_at', 'updated_at')
    search_fields = ('agency__full_name', 'agency__email', 'agency_member__name', 'website')
    readonly_fields = ('created_at', 'updated_at', 'total_images_display', 'total_videos_display', 'total_page_urls_display')

    @admin.display(description='Total Images')
    def total_images_display(self, obj):
        return obj.total_images

    @admin.display(description='Total Videos')
    def total_videos_display(self, obj):
        return obj.total_videos

    @admin.display(description='Total Page URLs')
    def total_page_urls_display(self, obj):
        return obj.total_page_urls


class AgencyMemberScanResultInline(TabularInline):
    per_page = 20
    model = AgencyMemberScanResult
    fk_name = 'agency_member'
    extra = 0
    show_change_link = True
    fields = ('website', 'status', 'total_images_display', 'total_videos_display', 'total_page_urls_display', 'created_at')
    readonly_fields = ('website', 'status', 'total_images_display', 'total_videos_display', 'total_page_urls_display', 'created_at')

    @admin.display(description='Total Images')
    def total_images_display(self, obj):
        return obj.total_images if obj else 0

    @admin.display(description='Total Videos')
    def total_videos_display(self, obj):
        return obj.total_videos if obj else 0

    @admin.display(description='Total Page URLs')
    def total_page_urls_display(self, obj):
        return obj.total_page_urls if obj else 0


@admin.register(AgencyMemberScanUserSummary)
class AgencyMemberScanUserSummaryAdmin(ModelAdmin):
    list_display = ('name', 'agency_email_display', 'total_websites_display', 'total_images_display', 'total_videos_display', 'total_page_urls_display', 'last_scanned_at_display')
    list_display_links = ('name', 'agency_email_display')
    search_fields = ('name', 'agency__email')
    readonly_fields = ('name', 'agency_email_display', 'total_websites_display', 'total_images_display', 'total_videos_display', 'total_page_urls_display')
    inlines = [AgencyMemberScanResultInline]
    list_select_related = ('agency',)
    list_per_page = 50

    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related('agency')
        img_sq = AgencyMemberScanResultImage.objects.filter(agency_member_scan_result__agency_member_id=OuterRef('pk')).values('agency_member_scan_result__agency_member_id').annotate(c=Count('id')).values('c')[:1]
        vid_sq = AgencyMemberScanResultVideo.objects.filter(agency_member_scan_result__agency_member_id=OuterRef('pk')).values('agency_member_scan_result__agency_member_id').annotate(c=Count('id')).values('c')[:1]
        url_sq = AgencyMemberScanResultPageUrl.objects.filter(agency_member_scan_result__agency_member_id=OuterRef('pk')).values('agency_member_scan_result__agency_member_id').annotate(c=Count('id')).values('c')[:1]
        web_sq = AgencyMemberScanResult.objects.filter(agency_member_id=OuterRef('pk')).values('agency_member_id').annotate(c=Count('id')).values('c')[:1]
        last_sq = AgencyMemberScanResult.objects.filter(agency_member_id=OuterRef('pk')).order_by('-created_at').values('created_at')[:1]
        return qs.filter(agency_member_scan_results__isnull=False).distinct().annotate(
            annotated_total_websites=Coalesce(Subquery(web_sq, output_field=IntegerField()), 0),
            annotated_total_images=Coalesce(Subquery(img_sq, output_field=IntegerField()), 0),
            annotated_total_videos=Coalesce(Subquery(vid_sq, output_field=IntegerField()), 0),
            annotated_total_page_urls=Coalesce(Subquery(url_sq, output_field=IntegerField()), 0),
            annotated_last_scanned_at=Subquery(last_sq),
        )

    @admin.display(description='Agency Email')
    def agency_email_display(self, obj):
        return obj.agency.email if obj.agency else "-"

    @admin.display(description='Total Websites Scanned')
    def total_websites_display(self, obj):
        if hasattr(obj, 'annotated_total_websites'):
            return obj.annotated_total_websites
        return obj.agency_member_scan_results.count()

    @admin.display(description='Total Images')
    def total_images_display(self, obj):
        if hasattr(obj, 'annotated_total_images'):
            return obj.annotated_total_images
        return sum(res.total_images for res in obj.agency_member_scan_results.all())

    @admin.display(description='Total Videos')
    def total_videos_display(self, obj):
        if hasattr(obj, 'annotated_total_videos'):
            return obj.annotated_total_videos
        return sum(res.total_videos for res in obj.agency_member_scan_results.all())

    @admin.display(description='Total Page URLs')
    def total_page_urls_display(self, obj):
        if hasattr(obj, 'annotated_total_page_urls'):
            return obj.annotated_total_page_urls
        return sum(res.total_page_urls for res in obj.agency_member_scan_results.all())

    @admin.display(description='Latest Scan')
    def last_scanned_at_display(self, obj):
        if hasattr(obj, 'annotated_last_scanned_at') and obj.annotated_last_scanned_at:
            return obj.annotated_last_scanned_at
        latest = obj.agency_member_scan_results.order_by('-created_at').first()
        return latest.created_at if latest else "-"

class AgencyMemberScanResultImageInline(TabularInline):
    per_page = 20
    model = AgencyMemberScanResultImage
    extra = 0
    readonly_fields = ('image_preview', 'image_url', 'image')
    fields = ('image_preview', 'image_url', 'image')

    @admin.display(description='Preview')
    def image_preview(self, obj):
        if not obj:
            return "No Image"
        url = obj.image.url if obj.image else obj.image_url
        if url:
            return format_html(
                '<img src="{}" style="max-width: 150px; max-height: 150px; object-fit: contain; border-radius: 4px;" />',
                url,
            )
        return "No Image"

class AgencyMemberScanResultVideoInline(TabularInline):
    per_page = 20
    model = AgencyMemberScanResultVideo
    extra = 0
    readonly_fields = ('video_url',)

class AgencyMemberScanResultPageUrlInline(TabularInline):
    per_page = 20
    model = AgencyMemberScanResultPageUrl
    extra = 0
    readonly_fields = ('page_url',)

AgencyMemberScanResultAdmin.inlines = [
    AgencyMemberScanResultImageInline,
    AgencyMemberScanResultVideoInline,
    AgencyMemberScanResultPageUrlInline
]

@admin.register(AgencyMemberScanResultImage)
class AgencyMemberScanResultImageAdmin(ModelAdmin):
    list_select_related = ('agency_member_scan_result', 'agency_member_scan_result__agency_member')
    list_per_page = 50
    list_display = ('id', 'agency_member_scan_result', 'image_preview', 'image_url')
    search_fields = ('image_url', 'agency_member_scan_result__website')
    readonly_fields = ('image_preview',)

    @admin.display(description='Preview')
    def image_preview(self, obj):
        if not obj:
            return "No Image"
        url = obj.image.url if obj.image else obj.image_url
        if url:
            return format_html(
                '<img src="{}" style="max-width: 150px; max-height: 150px; object-fit: contain; border-radius: 4px;" />',
                url,
            )
        return "No Image"


@admin.register(LinkRemovalRequestFromCustomer)
class LinkRemovalRequestFromCustomerAdmin(ModelAdmin):
    list_select_related = ('customer',)
    list_per_page = 50
    list_display = ('id', 'customer', 'clickable_link', 'status', 'links')
    search_fields = ('customer__email', 'link')
    list_filter = ('customer', 'status', 'links')
    list_display_links = ('id', 'customer', 'clickable_link')
    list_editable = ('status', 'links')
    actions = ['make_pending', 'make_removed', 'make_failed', 'send_dmca_notice_action', 'run_automated_verification']

    def save_model(self, request, obj, form, change):
        is_new = obj.pk is None
        super().save_model(request, obj, form, change)
        if is_new or obj.links == 'pending':
            from .tasks import enqueue_dmca_notice_for_request
            enqueue_dmca_notice_for_request(obj)
            enqueue_verification_for_request(obj)

    @admin.action(description='Send DMCA notice email for selected requests')
    def send_dmca_notice_action(self, request, queryset):
        from .tasks import enqueue_dmca_notice_for_request
        count = 0
        for obj in queryset:
            enqueue_dmca_notice_for_request(obj)
            count += 1
        self.message_user(request, f'Enqueued DMCA notice processing for {count} requests.')

    @admin.action(description='Mark selected requests as Pending')
    def make_pending(self, request, queryset):
        updated = queryset.update(status='pending')
        self.message_user(request, f'{updated} requests were successfully marked as Pending.')

    @admin.action(description='Mark selected requests as Removed')
    def make_removed(self, request, queryset):
        updated = queryset.update(status='removed')
        self.message_user(request, f'{updated} requests were successfully marked as Removed.')

    @admin.action(description='Mark selected requests as Failed')
    def make_failed(self, request, queryset):
        updated = queryset.update(status='failed')
        self.message_user(request, f'{updated} requests were successfully marked as Failed.')

    @admin.action(description='Run automated verification for selected requests')
    def run_automated_verification(self, request, queryset):
        count = 0
        for obj in queryset:
            enqueue_verification_for_request(obj)
            count += 1
        self.message_user(request, f'Enqueued automated background verification for {count} links.')

    def clickable_link(self, obj):
        return format_html(
            '<div style="display: flex; align-items: center; gap: 8px;">'
            '<a href="{}" target="_blank">{}</a>'
            '<button type="button" onclick="var btn=this; navigator.clipboard.writeText(this.dataset.link).then(function(){{var msg=btn.nextElementSibling; msg.style.display=\'inline\'; setTimeout(function(){{msg.style.display=\'none\';}}, 2000);}})" data-link="{}" style="background: none; border: none; cursor: pointer; padding: 0; color: #555;" title="Copy to clipboard">'
            '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16" style="width: 16px; height: 16px; min-width: 16px; pointer-events: none;">'
            '<path fill-rule="evenodd" d="M4 2a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V2Zm2-1a1 1 0 0 0-1 1v8a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1V2a1 1 0 0 0-1-1H6ZM2 5a1 1 0 0 0-1 1v8a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1v-1h1v1a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h1v1H2Z"/>'
            '</svg>'
            '</button>'
            '<span style="display: none; font-size: 12px; color: green; margin-left: 4px;">Copied!</span>'
            '</div>',
            obj.link,
            obj.link,
            obj.link
        )

    clickable_link.short_description = "Link"

@admin.register(LinkRemovalRequestFromAgencyMember)
class LinkRemovalRequestFromAgencyMemberAdmin(ModelAdmin):
    list_select_related = ('agency', 'agency_member')
    list_per_page = 50
    list_display = ('id', 'agency', 'agency_member', 'clickable_link', 'status', 'links')
    search_fields = ('agency__email', 'agency_member__name', 'link')
    list_filter = ('agency', 'agency_member', 'status', 'links')
    list_display_links = ('id', 'agency', 'agency_member', 'clickable_link')
    list_editable = ('status', 'links')
    actions = ['make_pending', 'make_removed', 'make_failed', 'send_dmca_notice_action', 'run_automated_verification']

    def save_model(self, request, obj, form, change):
        is_new = obj.pk is None
        super().save_model(request, obj, form, change)
        if is_new or obj.links == 'pending':
            from .tasks import enqueue_dmca_notice_for_request
            enqueue_dmca_notice_for_request(obj)
            enqueue_verification_for_request(obj)

    @admin.action(description='Send DMCA notice email for selected requests')
    def send_dmca_notice_action(self, request, queryset):
        from .tasks import enqueue_dmca_notice_for_request
        count = 0
        for obj in queryset:
            enqueue_dmca_notice_for_request(obj)
            count += 1
        self.message_user(request, f'Enqueued DMCA notice processing for {count} requests.')

    @admin.action(description='Mark selected requests as Pending')
    def make_pending(self, request, queryset):
        updated = queryset.update(status='pending')
        self.message_user(request, f'{updated} requests were successfully marked as Pending.')

    @admin.action(description='Mark selected requests as Removed')
    def make_removed(self, request, queryset):
        updated = queryset.update(status='removed')
        self.message_user(request, f'{updated} requests were successfully marked as Removed.')

    @admin.action(description='Mark selected requests as Failed')
    def make_failed(self, request, queryset):
        updated = queryset.update(status='failed')
        self.message_user(request, f'{updated} requests were successfully marked as Failed.')

    @admin.action(description='Run automated verification for selected requests')
    def run_automated_verification(self, request, queryset):
        count = 0
        for obj in queryset:
            enqueue_verification_for_request(obj)
            count += 1
        self.message_user(request, f'Enqueued automated background verification for {count} links.')

    def clickable_link(self, obj):
        return format_html(
            '<div style="display: flex; align-items: center; gap: 8px;">'
            '<a href="{}" target="_blank">{}</a>'
            '<button type="button" onclick="var btn=this; navigator.clipboard.writeText(this.dataset.link).then(function(){{var msg=btn.nextElementSibling; msg.style.display=\'inline\'; setTimeout(function(){{msg.style.display=\'none\';}}, 2000);}})" data-link="{}" style="background: none; border: none; cursor: pointer; padding: 0; color: #555;" title="Copy to clipboard">'
            '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16" style="width: 16px; height: 16px; min-width: 16px; pointer-events: none;">'
            '<path fill-rule="evenodd" d="M4 2a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V2Zm2-1a1 1 0 0 0-1 1v8a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1V2a1 1 0 0 0-1-1H6ZM2 5a1 1 0 0 0-1 1v8a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1v-1h1v1a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h1v1H2Z"/>'
            '</svg>'
            '</button>'
            '<span style="display: none; font-size: 12px; color: green; margin-left: 4px;">Copied!</span>'
            '</div>',
            obj.link,
            obj.link,
            obj.link
        )

    clickable_link.short_description = "Link"


@admin.register(LinkRemovalVerification)
class LinkRemovalVerificationAdmin(ModelAdmin):
    list_per_page = 50
    list_display = ('id', 'url', 'verification_status', 'http_status_code', 'retry_count', 'checked_at')
    search_fields = ('url', 'error_message')
    list_filter = ('verification_status', 'http_status_code')


@admin.register(CustomerScanResultPageUrl)
class CustomerScanResultPageUrlAdmin(ModelAdmin):
    list_select_related = ('customer_scan_result', 'customer_scan_result__customer')
    list_per_page = 50
    list_display = ('id', 'customer_scan_result', 'page_url', 'send_mail_status', 'created_at')
    search_fields = ('page_url', 'customer_scan_result__website', 'customer_scan_result__customer__email')
    list_filter = ('send_mail_status', 'customer_scan_result__website')
    list_editable = ('send_mail_status',)
    readonly_fields = ('created_at', 'updated_at')


@admin.register(AgencyMemberScanResultPageUrl)
class AgencyMemberScanResultPageUrlAdmin(ModelAdmin):
    list_select_related = ('agency_member_scan_result', 'agency_member_scan_result__agency_member')
    list_per_page = 50
    list_display = ('id', 'agency_member_scan_result', 'page_url', 'send_mail_status', 'created_at')
    search_fields = ('page_url', 'agency_member_scan_result__website', 'agency_member_scan_result__agency__email')
    list_filter = ('send_mail_status', 'agency_member_scan_result__website')
    list_editable = ('send_mail_status',)
    readonly_fields = ('created_at', 'updated_at')

