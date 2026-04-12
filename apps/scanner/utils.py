import os
import boto3
import requests
import uuid
import logging
from botocore.exceptions import ClientError
from django.core.mail import EmailMessage, get_connection
from io import BytesIO

logger = logging.getLogger(__name__)


def _get_smtp_connection():
    """
    Create an SMTP email connection using the active SMTPSetting from the database.
    Returns: (connection, from_email) or (None, None) if no active setting found.
    """
    from apps.system_setting.models import SMTPSetting

    smtp_setting = SMTPSetting.objects.filter(is_active=True).first()
    if not smtp_setting:
        logger.error("No active SMTP setting found in the database.")
        return None, None

    connection = get_connection(
        backend='django.core.mail.backends.smtp.EmailBackend',
        host=smtp_setting.host,
        port=smtp_setting.port,
        username=smtp_setting.username,
        password=smtp_setting.password,
        use_tls=smtp_setting.encryption == 'tls',
        use_ssl=smtp_setting.encryption == 'ssl',
    )

    # Format sender as "Name <email>" if sender_name is provided
    if smtp_setting.sender_name:
        from_email = f"{smtp_setting.sender_name} <{smtp_setting.sender_email}>"
    else:
        from_email = smtp_setting.sender_email

    return connection, from_email


def download_file(url):
    """
    Download a file from a URL.
    Returns: (content, content_type) or (None, None)
    """
    try:
        response = requests.get(url, timeout=30, stream=True)
        if response.status_code == 200:
            content = response.content
            content_type = response.headers.get('Content-Type')
            return content, content_type
    except Exception as e:
        logger.error(f"Error downloading {url}: {e}")
    
    return None, None

def send_dmca_notice(contact_emails, collected_data, creator_name):
    """
    Send DMCA takedown notice to specific emails.
    Uses SMTP credentials from the active SMTPSetting in the database.
    collected_data: {'images': [], 'videos': [], 'page_urls': []}
    """
    if not contact_emails:
        return False, "No contact emails provided"

    connection, from_email = _get_smtp_connection()
    if not connection:
        return False, "No active SMTP setting configured. Please activate one in System Settings."

    subject = f"DMCA Takedown Notice - Unauthorized Content of {creator_name}"
    
    # Construct Email Body
    site_links = "\n".join(collected_data.get('page_urls', []))
    image_links = "\n".join([img.get('original') for img in collected_data.get('images', [])])
    video_links = "\n".join(collected_data.get('videos', []))
    
    body = f"""
My name is Legal Compliance Team and I swear, under penalty of perjury, that the following information is accurate and that I am authorized to act on behalf of the owner ({creator_name}) whose rights are being infringed.

I request the removal of the following web page(s) and that all associated media (thumbnails, images, image galleries, and videos) are removed from your servers. If you are a registrar or CDN and receiving this complaint, it is due to your customer not being directly accessible via WHOIS. I kindly ask that you forward this complaint to your customer or provide contact information so that I may contact them directly.

{site_links}

I have a good faith belief that the use of the copyrighted materials, which are listed above, are not authorized by the copyright owner, its agent, or the law.

I understand that the information contained within this notification may be shared with third parties, the public, or the infringer who is the subject of this complaint.

As applicable under 17 U.S.C. 512(f), I acknowledge that I may be subject to liability for damages if I knowingly misrepresent the material or activity is infringing. 

Thank you.

Legal Compliance Team
For: {creator_name}
    """
    
    try:
        email = EmailMessage(
            subject=subject,
            body=body,
            from_email=from_email,
            to=contact_emails,
            connection=connection,
        )
        email.send(fail_silently=False)
        return True, "Email sent successfully"
    except Exception as e:
        logger.error(f"Email Error: {e}")
        return False, str(e)
