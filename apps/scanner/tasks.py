import logging
from celery import shared_task
from django.conf import settings
from django.template.loader import render_to_string
from apps.utils.helpers import send_email
from .models import (
    LinkRemovalRequestFromCustomer,
    LinkRemovalRequestFromAgencyMember,
    LinkRemovalVerification,
    UnauthorizedWebsiteAndEmail,
    CustomerScanResultPageUrl,
    AgencyMemberScanResultPageUrl,
)
from .verification import verify_url_availability
from .utils import send_dmca_notice, extract_domain_from_url

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_dmca_notice_task(self, request_id, request_type='customer'):
    """
    Celery background task to send DMCA notice for a removal request.
    Extracts the domain from the link, looks up the corresponding email from UnauthorizedWebsiteAndEmail,
    and sends the DMCA email via send_dmca_notice.
    """
    url = None
    creator_name = "Legal Compliance Team"

    if request_type == 'customer':
        try:
            req = LinkRemovalRequestFromCustomer.objects.get(id=request_id)
            url = req.link
            if req.customer:
                creator_name = req.customer.full_name or req.customer.username or "Content Creator"
        except LinkRemovalRequestFromCustomer.DoesNotExist:
            logger.error(f"LinkRemovalRequestFromCustomer #{request_id} not found.")
            return {'status': 'not_found'}

    elif request_type == 'agency':
        try:
            req = LinkRemovalRequestFromAgencyMember.objects.get(id=request_id)
            url = req.link
            if req.agency_member:
                creator_name = req.agency_member.name
            elif req.agency:
                creator_name = req.agency.full_name or req.agency.username
        except LinkRemovalRequestFromAgencyMember.DoesNotExist:
            logger.error(f"LinkRemovalRequestFromAgencyMember #{request_id} not found.")
            return {'status': 'not_found'}
    else:
        logger.error(f"Unknown request_type '{request_type}'.")
        return {'status': 'invalid_type'}

    if not url:
        return {'status': 'no_url'}

    domain = extract_domain_from_url(url)

    if getattr(req, 'links', 'pending') == 'submitted':
        logger.info(f"Link request #{request_id} for {url} is already marked as 'submitted'. Skipping email dispatch.")
        return {'status': 'already_submitted', 'domain': domain}

    if not domain:
        logger.warning(f"Could not extract domain from link: {url}")
        return {'status': 'domain_extraction_failed'}

    # Look up matching UnauthorizedWebsiteAndEmail entry by website domain
    record = UnauthorizedWebsiteAndEmail.objects.filter(website__iexact=domain).first()
    if not record:
        # Fallback partial lookup if domain contains website or vice versa
        record = UnauthorizedWebsiteAndEmail.objects.filter(website__icontains=domain).first()

    if not record or not record.email:
        logger.warning(f"No contact email found in UnauthorizedWebsiteAndEmail for domain '{domain}' (link: {url}).")
        return {'status': 'email_not_found', 'domain': domain}

    # Categorize link into collected_data
    lower_url = url.lower()
    images = []
    videos = []
    page_urls = [url]

    if any(ext in lower_url for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '/screenshots/']):
        images.append({'original': url})
    elif any(ext in lower_url for ext in ['.mp4', '.webm', '.avi', '.m3u8', '.mov']):
        videos.append(url)

    collected_data = {
        'page_urls': page_urls,
        'images': images,
        'videos': videos
    }

    success, msg = send_dmca_notice(
        contact_emails=[record.email],
        collected_data=collected_data,
        creator_name=creator_name
    )

    if success:
        req.links = 'submitted'
        req.save(update_fields=['links', 'updated_at'])
        if request_type == 'customer' and hasattr(req, 'customer') and req.customer:
            CustomerScanResultPageUrl.objects.filter(customer_scan_result__customer=req.customer, page_url=url).update(send_mail_status='submitted')
        elif request_type == 'agency' and hasattr(req, 'agency_member') and req.agency_member:
            AgencyMemberScanResultPageUrl.objects.filter(agency_member_scan_result__agency_member=req.agency_member, page_url=url).update(send_mail_status='submitted')
        logger.info(f"Successfully sent DMCA notice email to {record.email} for domain {domain} (Link #{request_id})")
        return {'status': 'email_sent', 'to': record.email, 'domain': domain}
    else:
        logger.error(f"Failed to send DMCA notice email to {record.email}: {msg}")
        return {'status': 'email_failed', 'error': msg}


def enqueue_dmca_notice_for_request(request_obj):
    """
    Helper function to enqueue a Celery task to send a DMCA notice email for a customer or agency request.
    """
    if isinstance(request_obj, LinkRemovalRequestFromCustomer):
        if getattr(settings, 'CELERY_TASK_ALWAYS_EAGER', False):
            return send_dmca_notice_task(request_obj.id, 'customer')
        else:
            return send_dmca_notice_task.delay(request_obj.id, 'customer')

    elif isinstance(request_obj, LinkRemovalRequestFromAgencyMember):
        if getattr(settings, 'CELERY_TASK_ALWAYS_EAGER', False):
            return send_dmca_notice_task(request_obj.id, 'agency')
        else:
            return send_dmca_notice_task.delay(request_obj.id, 'agency')
    return None


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def verify_link_removal_task(self, request_id, request_type='customer', retry_count=0):
    """
    Celery background task to directly verify a link removal request.
    """
    customer_request = None
    agency_request = None
    url = None
    recipient_email = None

    if request_type == 'customer':
        try:
            customer_request = LinkRemovalRequestFromCustomer.objects.get(id=request_id)
            url = customer_request.link
            recipient_email = customer_request.customer.email
            # Safe race condition check: If manually marked as removed by admin, do not overwrite
            if customer_request.status == 'removed':
                logger.info(f"Customer request #{request_id} is already marked as removed. Skipping verification.")
                return {'status': 'already_removed'}
        except LinkRemovalRequestFromCustomer.DoesNotExist:
            logger.error(f"LinkRemovalRequestFromCustomer #{request_id} not found.")
            return {'status': 'not_found'}

    elif request_type == 'agency':
        try:
            agency_request = LinkRemovalRequestFromAgencyMember.objects.get(id=request_id)
            url = agency_request.link
            recipient_email = agency_request.agency.email
            # Safe race condition check: If manually marked as removed by admin, do not overwrite
            if agency_request.status == 'removed':
                logger.info(f"Agency request #{request_id} is already marked as removed. Skipping verification.")
                return {'status': 'already_removed'}
        except LinkRemovalRequestFromAgencyMember.DoesNotExist:
            logger.error(f"LinkRemovalRequestFromAgencyMember #{request_id} not found.")
            return {'status': 'not_found'}

    else:
        logger.error(f"Unknown request_type '{request_type}'.")
        return {'status': 'invalid_type'}

    # Run direct HTTP verification
    verification_res = verify_url_availability(url)
    verification_status = verification_res['verification_status']

    # Record verification history entry
    verification_entry = LinkRemovalVerification.objects.create(
        customer_request=customer_request,
        agency_request=agency_request,
        url=url,
        http_status_code=verification_res['http_status_code'],
        final_url=verification_res['final_url'],
        content_type=verification_res['content_type'],
        verification_status=verification_status,
        retry_count=retry_count,
        error_message=verification_res['error_message'],
    )

    max_retries = getattr(settings, 'LINK_VERIFICATION_MAX_RETRIES', 3)
    retry_delays = getattr(settings, 'LINK_VERIFICATION_RETRY_DELAYS', [300, 1800, 7200])

    if verification_status == 'removed':
        # Update main removal request status to 'removed'
        if customer_request:
            customer_request.status = 'removed'
            customer_request.save(update_fields=['status', 'updated_at'])
        elif agency_request:
            agency_request.status = 'removed'
            agency_request.save(update_fields=['status', 'updated_at'])

        # Notify user via email
        if recipient_email:
            try:
                subject = "Link Removal Confirmed - Vantafy"
                body = f"Hello,\n\nYour requested link has been successfully removed:\n{url}\n\nThank you,\nVantafy Team"
                send_email(
                    subject=subject,
                    body=body,
                    to_emails=[recipient_email],
                    from_email=settings.DEFAULT_FROM_EMAIL
                )
            except Exception as e:
                logger.error(f"Failed to send removal email notification for link {url}: {e}")

    elif verification_status == 'temporarily_unavailable':
        # Retry policy for temporary failures
        if retry_count < max_retries:
            delay = retry_delays[min(retry_count, len(retry_delays) - 1)]
            logger.info(f"Temporary error verifying {url}. Retrying attempt #{retry_count + 1} in {delay}s...")

            # If CELERY_TASK_ALWAYS_EAGER is enabled (e.g. testing), run synchronously or queue retry
            if getattr(settings, 'CELERY_TASK_ALWAYS_EAGER', False):
                verify_link_removal_task(request_id, request_type, retry_count + 1)
            else:
                verify_link_removal_task.apply_async(
                    args=[request_id, request_type, retry_count + 1],
                    countdown=delay
                )

    return {
        'status': verification_status,
        'http_status_code': verification_res['http_status_code'],
        'verification_id': verification_entry.id
    }


def enqueue_verification_for_request(request_obj):
    """
    Helper function to enqueue a Celery verification task for a customer or agency request.
    """
    if isinstance(request_obj, LinkRemovalRequestFromCustomer):
        if getattr(settings, 'CELERY_TASK_ALWAYS_EAGER', False):
            return verify_link_removal_task(request_obj.id, 'customer', 0)
        else:
            return verify_link_removal_task.delay(request_obj.id, 'customer', 0)

    elif isinstance(request_obj, LinkRemovalRequestFromAgencyMember):
        if getattr(settings, 'CELERY_TASK_ALWAYS_EAGER', False):
            return verify_link_removal_task(request_obj.id, 'agency', 0)
        else:
            return verify_link_removal_task.delay(request_obj.id, 'agency', 0)
    return None


from celery import chain
from django.apps import apps
from django.core.cache import cache
from apps.subscriptions.models import Subscription, Package
from apps.user.models import AgencyMemberList
from .models import CustomerScanProcessing, AgencyMemberScanProcessing
from .services import run_all_spiders_sync


@shared_task(bind=True, max_retries=1)
def process_single_scan_job_task(self, scan_job_id, app_label, model_name, name_query, lock_key=None):
    """
    Celery task that synchronously executes spiders for a single scan job.
    Executes sequentially within a Celery chain, releasing any lock upon completion or failure.
    """
    logger.info(f"Starting sequential scan job execution: {model_name} #{scan_job_id} for query '{name_query}'")
    try:
        run_all_spiders_sync(
            name_query=name_query,
            job_id=scan_job_id,
            app_label=app_label,
            model_name=model_name
        )
        logger.info(f"Successfully finished scan job {model_name} #{scan_job_id}")
        return {'status': 'completed', 'job_id': scan_job_id}
    except Exception as e:
        logger.error(f"Error processing scan job {model_name} #{scan_job_id}: {e}")
        try:
            JobModel = apps.get_model(app_label, model_name)
            scan_job = JobModel.objects.get(id=scan_job_id)
            scan_job.status = 'failed'
            scan_job.error_message = str(e)
            scan_job.save(update_fields=['status', 'error_message', 'updated_at'])
        except Exception as save_err:
            logger.error(f"Failed to update error status for scan job #{scan_job_id}: {save_err}")
        return {'status': 'failed', 'job_id': scan_job_id, 'error': str(e)}
    finally:
        if lock_key:
            cache.delete(lock_key)


@shared_task
def run_daily_subscription_scans():
    """
    Master Celery Beat scheduled task for automated daily scans.
    Runs daily starting at 12:05 AM EST.
    Filters active subscriptions for Superstar, VIP, and Agency packages.
    Deduplicates active/pending jobs and queues jobs sequentially using Celery chain.
    """
    logger.info("Initializing daily scheduled subscription scan orchestrator...")

    # 1. Fetch active subscriptions with related packages and features
    active_subscriptions = Subscription.objects.filter(
        status='active'
    ).select_related('user', 'package').prefetch_related('package__features')

    def is_eligible_package(package):
        if not package:
            return False
        p_name = (package.name or '').strip().lower()
        p_type = package.type
        
        # Check Superstar, VIP, or Agency
        if 'superstar' in p_name or 'vip' in p_name or p_type == Package.PackageType.AGENCY or 'agency' in p_name:
            return True
            
        # Check if features include 'Daily Scans'
        if package.features.filter(name__iexact='Daily Scans').exists():
            return True
            
        return False

    task_signatures = []
    processed_customer_ids = set()
    processed_agency_member_ids = set()

    for sub in active_subscriptions:
        if not sub.user or not is_eligible_package(sub.package):
            continue

        user = sub.user
        role = getattr(user, 'role', None)

        if role == 'customer':
            if user.id in processed_customer_ids:
                continue
            processed_customer_ids.add(user.id)

            # Deduplication: Check if an active/pending scan job already exists for this customer
            has_active_job = CustomerScanProcessing.objects.filter(
                customer=user,
                status__in=['pending', 'running']
            ).exists()

            if has_active_job:
                logger.info(f"Skipping daily scan for Customer #{user.id} ({user.email}): active scan already in progress.")
                continue

            name_to_scan = user.full_name or user.username or user.email
            if not name_to_scan:
                continue

            lock_key = f"scan_lock_customer_{user.id}"
            # Safe cache lock: only skip if lock key actually exists in cache
            if cache.get(lock_key):
                logger.info(f"Lock active for Customer #{user.id}. Skipping.")
                continue
            try:
                cache.set(lock_key, "locked", timeout=86400)
            except Exception as cache_err:
                logger.warning(f"Could not write cache lock for Customer #{user.id}: {cache_err}")

            # Create scan job
            scan_job = CustomerScanProcessing.objects.create(
                customer=user,
                custom_search_name=name_to_scan,
                status='pending'
            )

            # Create immutable task signature for sequential chain
            sig = process_single_scan_job_task.si(
                scan_job.id,
                'scanner',
                'CustomerScanProcessing',
                name_to_scan,
                lock_key
            )
            task_signatures.append(sig)

        elif role == 'agency':
            # For agency users, scan all registered agency members
            members = AgencyMemberList.objects.filter(agency=user)
            for member in members:
                if member.id in processed_agency_member_ids:
                    continue
                processed_agency_member_ids.add(member.id)

                # Deduplication: Check if active/pending scan job exists for agency member
                has_active_job = AgencyMemberScanProcessing.objects.filter(
                    agency_member=member,
                    status__in=['pending', 'running']
                ).exists()

                if has_active_job:
                    logger.info(f"Skipping daily scan for AgencyMember #{member.id} ({member.name}): active scan already in progress.")
                    continue

                name_to_scan = member.name
                if not name_to_scan:
                    continue

                lock_key = f"scan_lock_agency_member_{member.id}"
                # Safe cache lock: only skip if lock key actually exists in cache
                if cache.get(lock_key):
                    logger.info(f"Lock active for AgencyMember #{member.id}. Skipping.")
                    continue
                try:
                    cache.set(lock_key, "locked", timeout=86400)
                except Exception as cache_err:
                    logger.warning(f"Could not write cache lock for AgencyMember #{member.id}: {cache_err}")

                # Create scan job
                scan_job = AgencyMemberScanProcessing.objects.create(
                    agency=user,
                    agency_member=member,
                    custom_search_name=name_to_scan,
                    status='pending'
                )

                # Create immutable task signature for sequential chain
                sig = process_single_scan_job_task.si(
                    scan_job.id,
                    'scanner',
                    'AgencyMemberScanProcessing',
                    name_to_scan,
                    lock_key
                )
                task_signatures.append(sig)

    if not task_signatures:
        logger.info("Daily subscription scan completed: No eligible targets to scan.")
        return {'status': 'no_targets', 'total_scheduled': 0}

    logger.info(f"Daily subscription scan orchestrator scheduled {len(task_signatures)} scan tasks to run sequentially.")

    # Execute sequentially using Celery chain or eager invocation if ALWAYS_EAGER is active
    if getattr(settings, 'CELERY_TASK_ALWAYS_EAGER', False):
        for sig in task_signatures:
            sig.apply()
    else:
        chain(*task_signatures).apply_async()

    return {'status': 'scheduled', 'total_scheduled': len(task_signatures)}


@shared_task
def send_weekly_subscription_email_reports():
    """
    Master Celery Beat scheduled task for sending weekly email reports to Starlet and Star subscribers.
    Runs every Sunday at 12:00 AM EST.
    Calculates number of new links discovered and number of links deleted in the past 7 days.
    """
    import datetime
    from django.utils import timezone

    logger.info("Initializing weekly subscription email report dispatch...")

    one_week_ago = timezone.now() - datetime.timedelta(days=7)

    active_subscriptions = Subscription.objects.filter(
        status='active'
    ).select_related('user', 'package').prefetch_related('package__features')

    def is_eligible_weekly_package(package):
        if not package:
            return False
        p_name = (package.name or '').strip().lower()
        if 'superstar' in p_name:
            return False
        if 'starlet' in p_name or 'star' in p_name:
            return True
        if package.features.filter(name__icontains='weekly').exists():
            return True
        return False

    processed_users = set()
    emails_sent_count = 0

    report_start_date = one_week_ago.strftime('%b %d, %Y')
    report_end_date = timezone.now().strftime('%b %d, %Y')

    for sub in active_subscriptions:
        if not sub.user or sub.user.id in processed_users or not is_eligible_weekly_package(sub.package):
            continue

        user = sub.user
        processed_users.add(user.id)

        role = getattr(user, 'role', None)

        new_links_count = 0
        deleted_links_count = 0

        if role == 'customer':
            new_links_count = CustomerScanResultPageUrl.objects.filter(
                customer_scan_result__customer=user,
                customer_scan_result__created_at__gte=one_week_ago
            ).count()

            deleted_links_count = LinkRemovalRequestFromCustomer.objects.filter(
                customer=user,
                status='removed',
                updated_at__gte=one_week_ago
            ).count()

        elif role == 'agency':
            new_links_count = AgencyMemberScanResultPageUrl.objects.filter(
                agency_member_scan_result__agency_member__agency=user,
                agency_member_scan_result__created_at__gte=one_week_ago
            ).count()

            deleted_links_count = LinkRemovalRequestFromAgencyMember.objects.filter(
                agency=user,
                status='removed',
                updated_at__gte=one_week_ago
            ).count()

        recipient_email = user.email
        if not recipient_email:
            continue

        context = {
            'user': user,
            'new_links_count': new_links_count,
            'deleted_links_count': deleted_links_count,
            'report_start_date': report_start_date,
            'report_end_date': report_end_date,
            'dashboard_url': getattr(settings, 'FRONTEND_URL', 'https://dashboard.vantafy.com'),
            'system_info': {'name': 'VantaFy', 'email': 'support@vantafy.com'}
        }

        try:
            html_message = render_to_string('email/weekly_report_template.html', context)
            subject = f"Your Weekly VantaFy Scan & Removal Report ({report_start_date} - {report_end_date})"

            user_display_name = getattr(user, 'full_name', None) or getattr(user, 'first_name', None) or user.email
            send_email(
                subject=subject,
                body=f"Hello {user_display_name},\n\nWeekly Summary:\nNew Links Discovered: {new_links_count}\nLinks Deleted: {deleted_links_count}\n\nVisit your dashboard: {context['dashboard_url']}",
                to_emails=[recipient_email],
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None),
                html_content=html_message
            )
            emails_sent_count += 1
            logger.info(f"Sent weekly email report to {recipient_email} (Discovered: {new_links_count}, Deleted: {deleted_links_count})")
        except Exception as e:
            logger.error(f"Failed to send weekly report email to {recipient_email}: {e}")

    return {'status': 'completed', 'total_emails_sent': emails_sent_count}


@shared_task
def run_weekly_subscription_scans():
    """
    Master Celery Beat scheduled task for automated weekly scans for Starlet and Star subscribers.
    Runs every Sunday at 12:00 PM EST.
    Filters active subscriptions for Starlet and Star packages.
    Deduplicates active/pending jobs and queues jobs sequentially using Celery chain.
    """
    logger.info("Initializing weekly scheduled subscription scan orchestrator for Starlet and Star...")

    active_subscriptions = Subscription.objects.filter(
        status='active'
    ).select_related('user', 'package').prefetch_related('package__features')

    def is_eligible_weekly_package(package):
        if not package:
            return False
        p_name = (package.name or '').strip().lower()
        if 'superstar' in p_name:
            return False
        if 'starlet' in p_name or 'star' in p_name:
            return True
        if package.features.filter(name__icontains='weekly').exists():
            return True
        return False

    task_signatures = []
    processed_customer_ids = set()
    processed_agency_member_ids = set()

    for sub in active_subscriptions:
        if not sub.user or not is_eligible_weekly_package(sub.package):
            continue

        user = sub.user
        role = getattr(user, 'role', None)

        if role == 'customer':
            if user.id in processed_customer_ids:
                continue
            processed_customer_ids.add(user.id)

            has_active_job = CustomerScanProcessing.objects.filter(
                customer=user,
                status__in=['pending', 'running']
            ).exists()

            if has_active_job:
                logger.info(f"Skipping weekly scan for Customer #{user.id} ({user.email}): active scan already in progress.")
                continue

            name_to_scan = user.full_name or user.username or user.email
            if not name_to_scan:
                continue

            lock_key = f"scan_lock_customer_{user.id}"
            if cache.get(lock_key):
                logger.info(f"Lock active for Customer #{user.id}. Skipping.")
                continue
            try:
                cache.set(lock_key, "locked", timeout=86400)
            except Exception as cache_err:
                logger.warning(f"Could not write cache lock for Customer #{user.id}: {cache_err}")

            scan_job = CustomerScanProcessing.objects.create(
                customer=user,
                custom_search_name=name_to_scan,
                status='pending'
            )

            sig = process_single_scan_job_task.si(
                scan_job.id,
                'scanner',
                'CustomerScanProcessing',
                name_to_scan,
                lock_key
            )
            task_signatures.append(sig)

        elif role == 'agency':
            members = AgencyMemberList.objects.filter(agency=user)
            for member in members:
                if member.id in processed_agency_member_ids:
                    continue
                processed_agency_member_ids.add(member.id)

                has_active_job = AgencyMemberScanProcessing.objects.filter(
                    agency_member=member,
                    status__in=['pending', 'running']
                ).exists()

                if has_active_job:
                    logger.info(f"Skipping weekly scan for AgencyMember #{member.id} ({member.name}): active scan already in progress.")
                    continue

                name_to_scan = member.name
                if not name_to_scan:
                    continue

                lock_key = f"scan_lock_agency_member_{member.id}"
                if cache.get(lock_key):
                    logger.info(f"Lock active for AgencyMember #{member.id}. Skipping.")
                    continue
                try:
                    cache.set(lock_key, "locked", timeout=86400)
                except Exception as cache_err:
                    logger.warning(f"Could not write cache lock for AgencyMember #{member.id}: {cache_err}")

                scan_job = AgencyMemberScanProcessing.objects.create(
                    agency=user,
                    agency_member=member,
                    custom_search_name=name_to_scan,
                    status='pending'
                )

                sig = process_single_scan_job_task.si(
                    scan_job.id,
                    'scanner',
                    'AgencyMemberScanProcessing',
                    name_to_scan,
                    lock_key
                )
                task_signatures.append(sig)

    if not task_signatures:
        logger.info("Weekly subscription scan completed: No eligible targets to scan.")
        return {'status': 'no_targets', 'total_scheduled': 0}

    logger.info(f"Weekly subscription scan orchestrator scheduled {len(task_signatures)} scan tasks to run sequentially.")

    if getattr(settings, 'CELERY_TASK_ALWAYS_EAGER', False):
        for sig in task_signatures:
            sig.apply()
    else:
        chain(*task_signatures).apply_async()

    return {'status': 'scheduled', 'total_scheduled': len(task_signatures)}


@shared_task
def send_daily_subscription_email_reports():
    """
    Master Celery Beat scheduled task for sending daily email reports to Superstar, VIP, and Agency subscribers.
    Runs every day at 12:00 AM EST.
    Calculates number of new links discovered and number of links deleted in the past 24 hours.
    """
    import datetime
    from django.utils import timezone

    logger.info("Initializing daily subscription email report dispatch...")

    one_day_ago = timezone.now() - datetime.timedelta(days=1)

    active_subscriptions = Subscription.objects.filter(
        status='active'
    ).select_related('user', 'package').prefetch_related('package__features')

    def is_eligible_daily_package(package):
        if not package:
            return False
        p_name = (package.name or '').strip().lower()
        p_type = package.type

        if 'superstar' in p_name or 'vip' in p_name or p_type == Package.PackageType.AGENCY or 'agency' in p_name:
            return True

        if package.features.filter(name__icontains='daily').exists():
            return True

        return False

    processed_users = set()
    emails_sent_count = 0

    report_date = timezone.now().strftime('%b %d, %Y')

    for sub in active_subscriptions:
        if not sub.user or sub.user.id in processed_users or not is_eligible_daily_package(sub.package):
            continue

        user = sub.user
        processed_users.add(user.id)

        role = getattr(user, 'role', None)

        new_links_count = 0
        deleted_links_count = 0

        if role == 'customer':
            new_links_count = CustomerScanResultPageUrl.objects.filter(
                customer_scan_result__customer=user,
                customer_scan_result__created_at__gte=one_day_ago
            ).count()

            deleted_links_count = LinkRemovalRequestFromCustomer.objects.filter(
                customer=user,
                status='removed',
                updated_at__gte=one_day_ago
            ).count()

        elif role == 'agency':
            new_links_count = AgencyMemberScanResultPageUrl.objects.filter(
                agency_member_scan_result__agency_member__agency=user,
                agency_member_scan_result__created_at__gte=one_day_ago
            ).count()

            deleted_links_count = LinkRemovalRequestFromAgencyMember.objects.filter(
                agency=user,
                status='removed',
                updated_at__gte=one_day_ago
            ).count()

        recipient_email = user.email
        if not recipient_email:
            continue

        context = {
            'user': user,
            'new_links_count': new_links_count,
            'deleted_links_count': deleted_links_count,
            'report_date': report_date,
            'dashboard_url': getattr(settings, 'FRONTEND_URL', 'https://dashboard.vantafy.com'),
            'system_info': {'name': 'VantaFy', 'email': 'support@vantafy.com'}
        }

        try:
            html_message = render_to_string('email/daily_report_template.html', context)
            subject = f"Your Daily VantaFy Scan & Removal Report ({report_date})"

            user_display_name = getattr(user, 'full_name', None) or getattr(user, 'first_name', None) or user.email
            send_email(
                subject=subject,
                body=f"Hello {user_display_name},\n\nDaily Summary:\nNew Links Discovered: {new_links_count}\nLinks Deleted: {deleted_links_count}\n\nVisit your dashboard: {context['dashboard_url']}",
                to_emails=[recipient_email],
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None),
                html_content=html_message
            )
            emails_sent_count += 1
            logger.info(f"Sent daily email report to {recipient_email} (Discovered: {new_links_count}, Deleted: {deleted_links_count})")
        except Exception as e:
            logger.error(f"Failed to send daily report email to {recipient_email}: {e}")

    return {'status': 'completed', 'total_emails_sent': emails_sent_count}



