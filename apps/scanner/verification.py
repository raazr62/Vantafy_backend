import logging
from urllib.parse import urlparse
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

MEDIA_EXTENSIONS = (
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg',
    '.mp4', '.mkv', '.webm', '.mov', '.avi', '.flv', '.wmv', '.m4v'
)

REMOVAL_STATUS_CODES = {404, 410, 451}
TEMPORARY_STATUS_CODES = {408, 429, 500, 502, 503, 504, 508}
BLOCKED_STATUS_CODES = {401, 403}


def is_direct_media_url(url: str) -> bool:
    """Check if the URL points directly to a media file based on extension."""
    parsed = urlparse(url)
    path = parsed.path.lower()
    return any(path.endswith(ext) for ext in MEDIA_EXTENSIONS)


def is_homepage_redirect(original_url: str, final_url: str) -> bool:
    """
    Check if a redirect targeted the root homepage or generic landing page,
    which is a standard pattern when a specific content item is deleted.
    """
    if not final_url:
        return False

    orig_parsed = urlparse(original_url)
    final_parsed = urlparse(final_url)

    # Normalize paths
    orig_path = orig_parsed.path.rstrip('/')
    final_path = final_parsed.path.rstrip('/')

    # If original URL had a deep path (e.g. /user/video123), but final URL is root '' or '/' or '/home' or '/index.html'
    if orig_path and orig_path != final_path:
        if final_path in ('', '/', '/home', '/index.html', '/main', '/en', '/default.aspx'):
            return True
    return False


def verify_url_availability(url: str) -> dict:
    """
    Directly checks the given URL using HTTP requests.
    Returns a dictionary with:
      - verification_status: 'removed', 'available', 'temporarily_unavailable', 'blocked', 'unverified'
      - http_status_code: int or None
      - final_url: str
      - content_type: str
      - error_message: str
    """
    user_agent = getattr(
        settings,
        'LINK_VERIFICATION_USER_AGENT',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    )
    timeout = getattr(settings, 'LINK_VERIFICATION_REQUEST_TIMEOUT', 15)

    headers = {
        'User-Agent': user_agent,
        'Accept': '*/*',
    }

    result = {
        'verification_status': 'unverified',
        'http_status_code': None,
        'final_url': url,
        'content_type': '',
        'error_message': '',
    }

    try:
        response = None
        is_media = is_direct_media_url(url)

        # Step 1: Try HEAD request for direct media files
        if is_media:
            try:
                head_resp = requests.head(
                    url,
                    headers=headers,
                    allow_redirects=True,
                    timeout=timeout,
                )
                if head_resp.status_code != 405:  # Method Not Allowed
                    response = head_resp
            except Exception as e:
                logger.debug(f"HEAD request failed for {url}: {e}")

        # Step 2: GET request (streamed for media, full for web pages)
        if response is None:
            response = requests.get(
                url,
                headers=headers,
                allow_redirects=True,
                timeout=timeout,
                stream=is_media
            )

        result['http_status_code'] = response.status_code
        result['final_url'] = response.url
        result['content_type'] = response.headers.get('Content-Type', '').split(';')[0].strip()

        status_code = response.status_code

        # Evaluate HTTP status code & redirect behavior
        if status_code in REMOVAL_STATUS_CODES:
            result['verification_status'] = 'removed'

        elif status_code in TEMPORARY_STATUS_CODES:
            result['verification_status'] = 'temporarily_unavailable'

        elif status_code in BLOCKED_STATUS_CODES:
            result['verification_status'] = 'blocked'

        elif 200 <= status_code < 300:
            # Check if there was a redirect to homepage (e.g. 302 -> 200 homepage)
            if response.history and is_homepage_redirect(url, response.url):
                result['verification_status'] = 'removed'
            else:
                result['verification_status'] = 'available'

        else:
            result['verification_status'] = 'unverified'

    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as exc:
        logger.warning(f"Connection/Timeout error verifying {url}: {exc}")
        result['verification_status'] = 'temporarily_unavailable'
        result['error_message'] = str(exc)

    except requests.exceptions.TooManyRedirects as exc:
        logger.warning(f"Too many redirects verifying {url}: {exc}")
        result['verification_status'] = 'removed'
        result['error_message'] = str(exc)

    except Exception as exc:
        logger.error(f"Unexpected error verifying {url}: {exc}")
        result['verification_status'] = 'unverified'
        result['error_message'] = str(exc)

    return result
