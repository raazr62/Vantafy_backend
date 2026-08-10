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
