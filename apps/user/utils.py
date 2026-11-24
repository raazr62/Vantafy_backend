import secrets
from django.core.mail import EmailMessage
from django.conf import settings
import hashlib
from apps.utils.helpers import success


def generate_otp(length=6):
    digits = '0123456789'
    return ''.join(secrets.choice(digits) for _ in range(length))

def send_normal_mail(data):
    from apps.system_setting.email_backend import get_active_from_email
    from_email = get_active_from_email()
    email = EmailMessage(
        subject=data['subject'],
        body=data['body'],
        from_email=from_email,
        to=data['to']
    )
    email.send()

def get_client_ip(request):
    """
    Get the client authentication IP address from specific request object.
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_user_agent_hash(request):
    """
    Get the SHA-256 hash of the User-Agent string.
    """
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    if not user_agent:
        return None
    
    # Hash the user agent
    hash_object = hashlib.sha256(user_agent.encode('utf-8'))
    return hash_object.hexdigest()


# ============================================
# Hybrid Authentication Response Utilities
# ============================================

def set_auth_cookies(response, access_token, refresh_token, secure=False, request=None):
    
    # Get domain setting from Django settings
    domain = getattr(settings, 'SESSION_COOKIE_DOMAIN', None)
    
    # Determine secure & samesite dynamically based on connection type
    if request is not None and request.is_secure():
        secure_flag = True
        samesite = getattr(settings, 'CSRF_COOKIE_SAMESITE', 'None')
    elif not settings.DEBUG and getattr(settings, 'SESSION_COOKIE_SECURE', False):
        secure_flag = True
        samesite = getattr(settings, 'CSRF_COOKIE_SAMESITE', 'None')
    else:
        # On HTTP connections, Secure MUST be False and SameSite MUST be Lax for browsers to store cookies
        secure_flag = False
        samesite = 'Lax'

    # Access token cookie
    response.set_cookie(
        key='access_token',
        value=access_token,
        domain=domain,  # None = current domain, '.domain.com' = all subdomains
        httponly=True,  # XSS protection
        secure=secure_flag,  # HTTPS only when secure
        samesite=samesite,  # CSRF protection
        max_age=getattr(settings, 'ACCESS_TOKEN_COOKIE_MAX_AGE', 3600)  # 1 hour default
    )
    
    # Refresh token cookie
    if refresh_token:
        response.set_cookie(
            key='refresh_token',
            value=refresh_token,
            domain=domain,  # None = current domain, '.domain.com' = all subdomains
            httponly=True,  # XSS protection
            secure=secure_flag,  # HTTPS only when secure
            samesite=samesite,  # CSRF protection
            max_age=getattr(settings, 'REFRESH_TOKEN_COOKIE_MAX_AGE', 86400 * 7)  # 7 days default
        )
    
    return response


def clear_auth_cookies(response, request=None):

    domain = getattr(settings, 'SESSION_COOKIE_DOMAIN', None)
    if request is not None and request.is_secure():
        secure_flag = True
        samesite = getattr(settings, 'CSRF_COOKIE_SAMESITE', 'None')
    elif not settings.DEBUG and getattr(settings, 'SESSION_COOKIE_SECURE', False):
        secure_flag = True
        samesite = getattr(settings, 'CSRF_COOKIE_SAMESITE', 'None')
    else:
        secure_flag = False
        samesite = 'Lax'
    
    # Manually expire cookies to support 'secure' attribute which delete_cookie may not accept
    response.set_cookie(
        'access_token', 
        value='', 
        max_age=0, 
        expires='Thu, 01 Jan 1970 00:00:00 GMT', 
        domain=domain, 
        samesite=samesite, 
        secure=secure_flag,
        httponly=True 
    )
    response.set_cookie(
        'refresh_token', 
        value='', 
        max_age=0, 
        expires='Thu, 01 Jan 1970 00:00:00 GMT', 
        domain=domain, 
        samesite=samesite, 
        secure=secure_flag, 
        httponly=True
    )
    return response


def create_hybrid_auth_response(data, tokens, request, message="Authentication successful", status_code=200):
   
    is_mobile = getattr(request, 'is_mobile_client', False)
    
    response_data = {
        'user': data,
        'tokens': {
            'access': tokens['access'],
            'refresh': tokens['refresh']
        }
    }
    response = success(
        data=response_data,
        message=message,
        status_code=status_code
    )
    
    if not is_mobile:
        set_auth_cookies(response, tokens['access'], tokens['refresh'], request=request)
    
    return response


def create_hybrid_refresh_response(tokens, request, message="Token refreshed successfully", status_code=200):
  
    is_mobile = getattr(request, 'is_mobile_client', False)
    
    response_data = {
        'tokens': {
            'access': tokens['access'],
            'refresh': tokens.get('refresh')  
        }
    }
    response = success(
        data=response_data,
        message=message,
        status_code=status_code
    )
    
    if not is_mobile:
        set_auth_cookies(response, tokens['access'], tokens.get('refresh'), request=request)
            
    return response
