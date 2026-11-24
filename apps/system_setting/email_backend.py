import logging
from django.core.mail.backends.smtp import EmailBackend
from django.conf import settings

logger = logging.getLogger(__name__)


def get_active_smtp_setting():
    """Fetch the active SMTPSetting from the database."""
    try:
        from apps.system_setting.models import SMTPSetting
        return SMTPSetting.objects.filter(is_active=True).first()
    except Exception as e:
        logger.warning(f"Could not load SMTPSetting from database: {e}")
        return None


def get_active_from_email():
    """Return sender formatted as 'Name <email>' or 'email' from active SMTPSetting or settings fallback."""
    active_smtp = get_active_smtp_setting()
    if active_smtp and active_smtp.sender_email:
        if active_smtp.sender_name:
            return f"{active_smtp.sender_name} <{active_smtp.sender_email}>"
        return active_smtp.sender_email
    return getattr(settings, 'DEFAULT_FROM_EMAIL', None) or getattr(settings, 'EMAIL_HOST_USER', '')


class DynamicSMTPEmailBackend(EmailBackend):
    """
    Custom Django Email Backend that dynamically loads host, port, username, password,
    and encryption settings from the active SMTPSetting model in the admin dashboard.
    """
    def __init__(self, host=None, port=None, username=None, password=None,
                 use_tls=None, fail_silently=False, use_ssl=None, timeout=None,
                 ssl_keyfile=None, ssl_certfile=None, **kwargs):

        active_smtp = get_active_smtp_setting()
        if active_smtp:
            host = host or active_smtp.host
            port = port or active_smtp.port
            username = username or active_smtp.username
            password = password or active_smtp.password
            if use_tls is None and use_ssl is None:
                use_tls = (active_smtp.encryption == 'tls')
                use_ssl = (active_smtp.encryption == 'ssl')

        super().__init__(
            host=host,
            port=port,
            username=username,
            password=password,
            use_tls=use_tls,
            fail_silently=fail_silently,
            use_ssl=use_ssl,
            timeout=timeout,
            ssl_keyfile=ssl_keyfile,
            ssl_certfile=ssl_certfile,
            **kwargs
        )
