import os
import boto3
import requests
import uuid
import logging
from botocore.exceptions import ClientError
from django.conf import settings
from django.core.mail import send_mail
from io import BytesIO

logger = logging.getLogger(__name__)



def send_dmca_notice(contact_emails, collected_data, creator_name):
    """
    Send DMCA takedown notice to specific emails.
    collected_data: {'images': [], 'videos': [], 'page_urls': []}
    """
    if not contact_emails:
        return False, "No contact emails provided"
        
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
        send_mail(
            subject,
            body,
            settings.DEFAULT_FROM_EMAIL,
            contact_emails,
            fail_silently=False,
        )
        return True, "Email sent successfully"
    except Exception as e:
        logger.error(f"Email Error: {e}")
        return False, str(e)
