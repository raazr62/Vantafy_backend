from django.contrib import admin, messages as django_messages
from django.urls import path
from django.shortcuts import render, redirect
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
        from .models import (
            CustomerScanProcessing,
            CustomerScanResult,
            CustomerScanResultPageUrl,
            AgencyMemberScanProcessing,
            AgencyMemberScanResult,
            AgencyMemberScanResultPageUrl,
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
                return redirect(request.path)

            elif action == "delete_images":
                if selected_image_ids:
                    from .models import CustomerScanResultImage, AgencyMemberScanResultImage
                    c_deleted, _ = CustomerScanResultImage.objects.filter(id__in=selected_image_ids).delete()
                    a_deleted, _ = AgencyMemberScanResultImage.objects.filter(id__in=selected_image_ids).delete()
                    total_deleted = c_deleted + a_deleted
                    django_messages.success(request, f"Successfully deleted {total_deleted} selected image(s).")
                else:
                    django_messages.warning(request, "No images were selected for deletion.")
                return redirect(request.path)

            elif action == "send_mail":
                if selected_ids:
                    from .tasks import enqueue_dmca_notice_for_request, enqueue_verification_for_request
                    from .models import LinkRemovalRequestFromCustomer, LinkRemovalRequestFromAgencyMember

                    # Count already submitted links
                    already_submitted_c = CustomerScanResultPageUrl.objects.filter(id__in=selected_ids, send_mail_status='submitted').count()
                    already_submitted_a = AgencyMemberScanResultPageUrl.objects.filter(id__in=selected_ids, send_mail_status='submitted').count()
                    skipped_count = already_submitted_c + already_submitted_a

                    # Query unsubmitted page URLs
                    c_purls = CustomerScanResultPageUrl.objects.filter(id__in=selected_ids).exclude(send_mail_status='submitted').select_related('customer_scan_result__customer')
                    a_purls = AgencyMemberScanResultPageUrl.objects.filter(id__in=selected_ids).exclude(send_mail_status='submitted').select_related('agency_member_scan_result__agency', 'agency_member_scan_result__agency_member')

                    if not c_purls.exists() and not a_purls.exists():
                        django_messages.warning(request, f"The selected link(s) have already been submitted ({skipped_count} link(s) skipped). No duplicate emails were sent.")
                        return redirect(request.path)

                    sent_count = 0

                    # Process Customer page URLs
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

                    # Process Agency Member page URLs
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

                    if skipped_count > 0:
                        django_messages.success(request, f"Successfully sent mail for {sent_count} link(s). ({skipped_count} link(s) skipped because they were already submitted).")
                    else:
                        django_messages.success(request, f"Successfully sent mail for {sent_count} selected link(s). Status updated to Submitted.")
                else:
                    django_messages.warning(request, "No links were selected for sending emails.")
                return redirect(request.path)

            elif action == "add_manual_links":
                raw_links = request.POST.get("manual_links", "").strip()
                if not raw_links:
                    django_messages.warning(request, "Please enter at least one link.")
                    return redirect(request.path)

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

                        _, created = CustomerScanResultPageUrl.objects.get_or_create(
                            customer_scan_result=scan_res,
                            page_url=formatted_url,
                            defaults={'send_mail_status': 'pending'}
                        )
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

                        _, created = AgencyMemberScanResultPageUrl.objects.get_or_create(
                            agency_member_scan_result=scan_res,
                            page_url=formatted_url,
                            defaults={'send_mail_status': 'pending'}
                        )
                        if created:
                            added_count += 1

                if added_count > 0:
                    django_messages.success(request, f"Successfully added {added_count} manual link(s).")
                else:
                    django_messages.info(request, "No new unique links were added (the links may already exist).")
                return redirect(request.path)

        target_title = "Scan Details"
        target_subtitle = ""
        scan_type = "Individual"

        scan_results = []
        images = []
        page_urls = []

        if target_type == "customer":
            customer = User.objects.filter(id=target_id).first()
            if customer:
                target_title = customer.full_name or customer.email
                target_subtitle = f"Customer Scan Overview for {customer.email}"
                scan_type = "Individual Customer"
                results_qs = CustomerScanResult.objects.filter(customer=customer).annotate(
                    num_images=Count('image_entries', distinct=True),
                    num_videos=Count('video_entries', distinct=True),
                    num_page_urls=Count('page_url_entries', distinct=True)
                ).prefetch_related('image_entries', 'video_entries', 'page_url_entries')
                for res in results_qs:
                    c_url = reverse('admin:scanner_customerscanresult_change', args=[res.id])
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

                    for img in res.image_entries.all():
                        images.append({
                            'id': img.id,
                            'image_url': img.image_url,
                            'display_url': img.image_url or (img.image.url if img.image.name else ''),
                            'website': res.website,
                        })

                    for p_url in res.page_url_entries.all():
                        page_urls.append({
                            'id': p_url.id,
                            'page_url': p_url.page_url,
                            'website': res.website,
                            'send_mail_status': getattr(p_url, 'send_mail_status', 'pending'),
                            'send_mail_status_display': p_url.get_send_mail_status_display() if hasattr(p_url, 'get_send_mail_status_display') else 'Pending',
                        })

        elif target_type == "agency_member":
            member = AgencyMemberList.objects.select_related('agency').filter(id=target_id).first()
            if member:
                target_title = member.name
                agency_email = member.agency.email if member.agency else ""
                target_subtitle = f"Agency Member Scan Overview ({agency_email})"
                scan_type = "Agency Member"
                results_qs = AgencyMemberScanResult.objects.filter(agency_member=member).annotate(
                    num_images=Count('image_entries', distinct=True),
                    num_videos=Count('video_entries', distinct=True),
                    num_page_urls=Count('page_url_entries', distinct=True)
                ).prefetch_related('image_entries', 'video_entries', 'page_url_entries')
                for res in results_qs:
                    c_url = reverse('admin:scanner_agencymemberscanresult_change', args=[res.id])
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

                    for img in res.image_entries.all():
                        images.append({
                            'id': img.id,
                            'image_url': img.image_url,
                            'display_url': img.image_url or (img.image.url if img.image.name else ''),
                            'website': res.website,
                        })

                    for p_url in res.page_url_entries.all():
                        page_urls.append({
                            'id': p_url.id,
                            'page_url': p_url.page_url,
                            'website': res.website,
                            'send_mail_status': getattr(p_url, 'send_mail_status', 'pending'),
                            'send_mail_status_display': p_url.get_send_mail_status_display() if hasattr(p_url, 'get_send_mail_status_display') else 'Pending',
                        })

        elif target_type == "customer_job":
            job = CustomerScanProcessing.objects.select_related('customer').filter(id=target_id).first()
            if job:
                target_title = job.search_name
                c_email = job.customer.email if job.customer else "-"
                target_subtitle = f"Individual Scan Run #{job.id} for {c_email}"
                scan_type = "Individual Execution"
                results_qs = job.results.all().annotate(
                    num_images=Count('image_entries', distinct=True),
                    num_videos=Count('video_entries', distinct=True),
                    num_page_urls=Count('page_url_entries', distinct=True)
                ).prefetch_related('image_entries', 'video_entries', 'page_url_entries')
                for res in results_qs:
                    c_url = reverse('admin:scanner_customerscanresult_change', args=[res.id])
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

                    for img in res.image_entries.all():
                        images.append({
                            'id': img.id,
                            'image_url': img.image_url,
                            'display_url': img.image.url or (img.image.url if img.image.name else ''),
                            'website': res.website,
                        })

                    for p_url in res.page_url_entries.all():
                        page_urls.append({
                            'id': p_url.id,
                            'page_url': p_url.page_url,
                            'website': res.website,
                            'send_mail_status': getattr(p_url, 'send_mail_status', 'pending'),
                            'send_mail_status_display': p_url.get_send_mail_status_display() if hasattr(p_url, 'get_send_mail_status_display') else 'Pending',
                        })

        elif target_type == "agency_job":
            job = AgencyMemberScanProcessing.objects.select_related('agency', 'agency_member').filter(id=target_id).first()
            if job:
                target_title = job.search_name
                a_email = job.agency.email if job.agency else "-"
                target_subtitle = f"Agency Scan Run #{job.id} for {a_email}"
                scan_type = "Agency Execution"
                results_qs = job.results.all().annotate(
                    num_images=Count('image_entries', distinct=True),
                    num_videos=Count('video_entries', distinct=True),
                    num_page_urls=Count('page_url_entries', distinct=True)
                ).prefetch_related('image_entries', 'video_entries', 'page_url_entries')
                for res in results_qs:
                    c_url = reverse('admin:scanner_agencymemberscanresult_change', args=[res.id])
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

                    for img in res.image_entries.all():
                        images.append({
                            'id': img.id,
                            'image_url': img.image_url,
                            'display_url': img.image_url or (img.image.url if img.image.name else ''),
                            'website': res.website,
                        })

                    for p_url in res.page_url_entries.all():
                        page_urls.append({
                            'id': p_url.id,
                            'page_url': p_url.page_url,
                            'website': res.website,
                            'send_mail_status': getattr(p_url, 'send_mail_status', 'pending'),
                            'send_mail_status_display': p_url.get_send_mail_status_display() if hasattr(p_url, 'get_send_mail_status_display') else 'Pending',
                        })

        context = {
            **self.admin_site.each_context(request),
            "title": f"Scan Details - {target_title}",
            "target_title": target_title,
            "target_subtitle": target_subtitle,
            "scan_type": scan_type,
            "page_urls": page_urls,
            "images": images,
            "scan_results": scan_results,
            "opts": self.model._meta,
        }
        return render(request, "admin/scanner/scan_detail.html", context)

    def admin_all_scans_view(self, request):
        from django.urls import reverse
        from datetime import datetime

        search_query = request.GET.get('q', '').strip()
        scan_type_filter = request.GET.get('scan_type', '').strip()
        view_mode = request.GET.get('view_mode', 'grouped').strip()

        from django.db.models import Count

        customer_scans = CustomerScanProcessing.objects.select_related('customer').annotate(
            num_images=Count('results__image_entries', distinct=True),
            num_videos=Count('results__video_entries', distinct=True),
            num_page_urls=Count('results__page_url_entries', distinct=True),
        ).all()
        agency_scans = AgencyMemberScanProcessing.objects.select_related('agency', 'agency_member').annotate(
            num_images=Count('results__image_entries', distinct=True),
            num_videos=Count('results__video_entries', distinct=True),
            num_page_urls=Count('results__page_url_entries', distinct=True),
        ).all()

        detailed_scans = []

        for item in customer_scans:
            c_name = item.search_name
            if c_name == "Unknown" and item.customer:
                c_name = item.customer.full_name or item.customer.email
            c_email = item.customer.email if item.customer else "-"
            last_time = item.completed_at or item.updated_at or item.created_at

            detail_url = reverse('admin:scanner_scan_detail', kwargs={'target_type': 'customer_job', 'target_id': item.id})

            detailed_scans.append({
                'id': item.id,
                'target_type': 'customer',
                'target_id': item.customer_id,
                'group_key': ('Individual', item.customer_id or item.search_name),
                'customer_name': c_name,
                'customer_email': c_email,
                'scan_type': 'Individual',
                'status': item.get_status_display(),
                'status_raw': item.status,
                'last_scan_time': last_time,
                'total_images': item.total_images,
                'total_videos': item.total_videos,
                'total_page_urls': item.total_page_urls,
                'detail_url': detail_url,
            })

        for item in agency_scans:
            c_name = item.search_name
            if c_name == "Unknown" and item.agency_member:
                c_name = item.agency_member.name
            c_email = item.agency.email if item.agency else "-"
            last_time = item.completed_at or item.updated_at or item.created_at

            detail_url = reverse('admin:scanner_scan_detail', kwargs={'target_type': 'agency_job', 'target_id': item.id})

            detailed_scans.append({
                'id': item.id,
                'target_type': 'agency_member',
                'target_id': item.agency_member_id,
                'group_key': ('Agency', item.agency_member_id or item.search_name),
                'customer_name': c_name,
                'customer_email': c_email,
                'scan_type': 'Agency',
                'status': item.get_status_display(),
                'status_raw': item.status,
                'last_scan_time': last_time,
                'total_images': item.total_images,
                'total_videos': item.total_videos,
                'total_page_urls': item.total_page_urls,
                'detail_url': detail_url,
            })

        if search_query:
            q_lower = search_query.lower()
            detailed_scans = [
                s for s in detailed_scans
                if q_lower in s['customer_name'].lower() or q_lower in s['customer_email'].lower()
            ]

        if scan_type_filter in ['Individual', 'Agency']:
            detailed_scans = [s for s in detailed_scans if s['scan_type'] == scan_type_filter]

        groups_dict = {}
        for s in detailed_scans:
            g_key = s['group_key']
            if g_key not in groups_dict:
                t_type = s['target_type']
                t_id = s['target_id']
                if t_id and t_type == 'customer':
                    group_detail_url = reverse('admin:scanner_scan_detail', kwargs={'target_type': 'customer', 'target_id': t_id})
                elif t_id and t_type == 'agency_member':
                    group_detail_url = reverse('admin:scanner_scan_detail', kwargs={'target_type': 'agency_member', 'target_id': t_id})
                else:
                    group_detail_url = s['detail_url']

                groups_dict[g_key] = {
                    'customer_name': s['customer_name'],
                    'customer_email': s['customer_email'],
                    'scan_type': s['scan_type'],
                    'total_scans': 0,
                    'last_scan_time': s['last_scan_time'],
                    'status': s['status'],
                    'status_raw': s['status_raw'],
                    'total_images': 0,
                    'total_videos': 0,
                    'total_page_urls': 0,
                    'scans': [],
                    'detail_url': group_detail_url,
                }

            group = groups_dict[g_key]
            group['total_scans'] += 1
            group['total_images'] += s['total_images']
            group['total_videos'] += s['total_videos']
            group['total_page_urls'] += s['total_page_urls']
            group['scans'].append(s)

            if s['last_scan_time'] and (group['last_scan_time'] is None or s['last_scan_time'] > group['last_scan_time']):
                group['last_scan_time'] = s['last_scan_time']
                group['status'] = s['status']
                group['status_raw'] = s['status_raw']

        grouped_scans = list(groups_dict.values())
        grouped_scans.sort(key=lambda x: x['last_scan_time'] if x['last_scan_time'] else datetime.min, reverse=True)
        detailed_scans.sort(key=lambda x: x['last_scan_time'] if x['last_scan_time'] else datetime.min, reverse=True)

        context = {
            **self.admin_site.each_context(request),
            "title": "All Scans Overview",
            "grouped_scans": grouped_scans,
            "detailed_scans": detailed_scans,
            "view_mode": view_mode,
            "search_query": search_query,
            "scan_type_filter": scan_type_filter,
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

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(customer_scan_results__isnull=False).distinct()

    @admin.display(description='Total Websites Scanned')
    def total_websites_display(self, obj):
        return obj.customer_scan_results.count()

    @admin.display(description='Total Images')
    def total_images_display(self, obj):
        return sum(res.total_images for res in obj.customer_scan_results.all())

    @admin.display(description='Total Videos')
    def total_videos_display(self, obj):
        return sum(res.total_videos for res in obj.customer_scan_results.all())

    @admin.display(description='Total Page URLs')
    def total_page_urls_display(self, obj):
        return sum(res.total_page_urls for res in obj.customer_scan_results.all())

    @admin.display(description='Latest Scan')
    def last_scanned_at_display(self, obj):
        latest = obj.customer_scan_results.order_by('-created_at').first()
        return latest.created_at if latest else "-"



# -------------------------
# Inlines for Scan Result Images/Videos/URLs
# -------------------------
class CustomerScanResultImageInline(TabularInline):
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
    model = CustomerScanResultVideo
    extra = 0

class CustomerScanResultPageUrlInline(TabularInline):
    model = CustomerScanResultPageUrl
    extra = 0

CustomerScanResultAdmin.inlines = [
    CustomerScanResultImageInline,
    CustomerScanResultVideoInline,
    CustomerScanResultPageUrlInline
]

@admin.register(CustomerScanResultImage)
class CustomerScanResultImageAdmin(ModelAdmin):
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

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(agency_member_scan_results__isnull=False).distinct()

    @admin.display(description='Agency Email')
    def agency_email_display(self, obj):
        return obj.agency.email if obj.agency else "-"

    @admin.display(description='Total Websites Scanned')
    def total_websites_display(self, obj):
        return obj.agency_member_scan_results.count()

    @admin.display(description='Total Images')
    def total_images_display(self, obj):
        return sum(res.total_images for res in obj.agency_member_scan_results.all())

    @admin.display(description='Total Videos')
    def total_videos_display(self, obj):
        return sum(res.total_videos for res in obj.agency_member_scan_results.all())

    @admin.display(description='Total Page URLs')
    def total_page_urls_display(self, obj):
        return sum(res.total_page_urls for res in obj.agency_member_scan_results.all())

    @admin.display(description='Latest Scan')
    def last_scanned_at_display(self, obj):
        latest = obj.agency_member_scan_results.order_by('-created_at').first()
        return latest.created_at if latest else "-"

class AgencyMemberScanResultImageInline(TabularInline):
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
    model = AgencyMemberScanResultVideo
    extra = 0
    readonly_fields = ('video_url',)

class AgencyMemberScanResultPageUrlInline(TabularInline):
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
    list_display = ('id', 'url', 'verification_status', 'http_status_code', 'retry_count', 'checked_at')
    search_fields = ('url', 'error_message')
    list_filter = ('verification_status', 'http_status_code')


@admin.register(CustomerScanResultPageUrl)
class CustomerScanResultPageUrlAdmin(ModelAdmin):
    list_display = ('id', 'customer_scan_result', 'page_url')
    search_fields = ('page_url', 'customer_scan_result__website', 'customer_scan_result__customer__email')


@admin.register(AgencyMemberScanResultPageUrl)
class AgencyMemberScanResultPageUrlAdmin(ModelAdmin):
    list_display = ('id', 'agency_member_scan_result', 'page_url')
    search_fields = ('page_url', 'agency_member_scan_result__website', 'agency_member_scan_result__agency__email')

