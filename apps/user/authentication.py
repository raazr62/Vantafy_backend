from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.authentication import CSRFCheck
from rest_framework import exceptions
from django.conf import settings

def enforce_csrf(request):
    """
    Enforce CSRF protection for cookie-based authentication.
    Only enabled for web clients using cookie authentication.
    """
    check = CSRFCheck(request)
    check.process_request(request)
    reason = check.process_view(request, None, (), {})
    if reason:
        raise exceptions.PermissionDenied(f'CSRF Failed: {reason}')


class HybridJWTAuthentication(JWTAuthentication):
    """
    Hybrid JWT Authentication supporting both:
    1. Web clients: HttpOnly cookies (access_token, refresh_token)
    2. Mobile clients: Authorization header (Bearer token)
    
    Priority:
    - Authorization header first (for mobile apps)
    - Cookies second (for web apps)
    - Falls back gracefully
    
    Security Features:
    - User-Agent binding (optional, configurable)
    - CSRF protection for cookie auth (optional, configurable)
    - Token validation
    """
    
    def authenticate(self, request):
        is_mobile = getattr(request, 'is_mobile_client', False)
        
        header = self.get_header(request)
        raw_token = None
        if header is not None:
            raw_token = self.get_raw_token(header)
            if raw_token is not None:
                temp_token = raw_token.decode('utf-8') if isinstance(raw_token, bytes) else str(raw_token)
                temp_token_clean = temp_token.strip('\'"')
                if temp_token_clean in ('null', 'undefined', '', 'None'):
                    raw_token = None

        # Step 2: Fallback to cookies (web clients)
        if raw_token is None:
            raw_token = request.COOKIES.get('access_token') or None

        if raw_token is None:
            return None
        
        # Ensure token is string and clean
        if isinstance(raw_token, bytes):
            raw_token = raw_token.decode('utf-8')
        
        # Strip potential quotes from cookie value
        raw_token = raw_token.strip('\'"')

        # Validate the token
        try:
            validated_token = self.get_validated_token(raw_token)
        except Exception:
            # Fallback: If access_token is expired/invalid, try using refresh_token cookie
            refresh_token_str = request.COOKIES.get('refresh_token')
            if refresh_token_str:
                refresh_token_str = refresh_token_str.strip('\'"')
                if refresh_token_str not in ('null', 'undefined', ''):
                    try:
                        from rest_framework_simplejwt.tokens import RefreshToken
                        rf = RefreshToken(refresh_token_str)
                        access_token_obj = rf.access_token
                        validated_token = self.get_validated_token(str(access_token_obj))
                    except Exception:
                        return None
                else:
                    return None
            else:
                return None

        # SECURITY: User-Agent binding validation
        if getattr(settings, 'ENABLE_USER_AGENT_BINDING', True):
            try:
                self._validate_user_agent(request, validated_token)
            except exceptions.AuthenticationFailed:
                if not getattr(settings, 'CROSS_ORIGIN_DEVELOPMENT', False):
                    return None

        # SECURITY: CSRF protection for cookie-based auth
        if not is_mobile and 'access_token' in request.COOKIES:
            if getattr(settings, 'ENABLE_CSRF_FOR_COOKIES', False):
                enforce_csrf(request)

        try:
            user = self.get_user(validated_token)
            if user is None:
                return None
            return user, validated_token
        except exceptions.AuthenticationFailed:
            return None

    def get_user(self, validated_token):
        try:
            return super().get_user(validated_token)
        except exceptions.AuthenticationFailed:
            return None

    def _validate_user_agent(self, request, validated_token):
        """
        Validate User-Agent binding to prevent token theft.
        Tokens are bound to the User-Agent that created them.
        """
        from .utils import get_user_agent_hash

        token_ua_hash = validated_token.get('user_agent')
        current_ua_hash = get_user_agent_hash(request)

        if token_ua_hash and token_ua_hash != current_ua_hash:
            # Log for security monitoring
            print(f"SECURITY WARNING: User-Agent Mismatch! Token UA: {token_ua_hash}, Request UA: {current_ua_hash}")
            raise exceptions.AuthenticationFailed('Token is invalid (User-Agent Mismatch).')


# Legacy alias for backward compatibility
CookieJWTAuthentication = HybridJWTAuthentication
