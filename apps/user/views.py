from rest_framework.exceptions import ValidationError
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

from apps.user.models import Niche
from .authentication import CookieJWTAuthentication
from .models import Niche, StageName
from .models import ConnectedSocialAccount





# Use hybrid response utility
from .utils import create_hybrid_auth_response

from .serializers import (
    ConnectedSocialAccountSerializer,
    SignUpSerializer,
    SignInSerializer,
    SignOutSerializer,
    ChangePasswordSerializer,
    SendOTPSerializer,
    ResendOTPSerializer,
    VerifyOTPSerializer,
    ResetPasswordSerializer,
    UpdataProfileAvatarSerializer,
)

from apps.utils.helpers import success, error


# Create your views here.
class SignUpView(APIView):
    permission_classes = []

    def post(self, request):

        serializer = SignUpSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            serializer.save()
            result = serializer.data
            
            
            tokens = {
                'access': result['access'],
                'refresh': result['refresh']
            }
            
            response = create_hybrid_auth_response(
                data=result['user'],
                tokens=tokens,
                request=request,
                message="Signup successful.",
                status_code=status.HTTP_201_CREATED
            )
            
            return response
        raise ValidationError(serializer.errors)

class SignInView(APIView):

    permission_classes = []

    def post(self, request):
        
        serializer = SignInSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            result = serializer.data
            
            
            tokens = {
                'access': result['access'],
                'refresh': result['refresh']
            }
            
            response = create_hybrid_auth_response(
                data=result['user'],
                tokens=tokens,
                request=request,
                message="Signin successful.",
                status_code=status.HTTP_200_OK
            )
            
            return response
        raise ValidationError(serializer.errors)


class SignOutView(APIView):
  
    
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieJWTAuthentication]

    def post(self, request):
        # Get tokens from request body or cookies
        data = request.data.copy()
        if 'refresh_token' not in data and 'refresh_token' in request.COOKIES:
            data['refresh_token'] = request.COOKIES['refresh_token']
        if 'access_token' not in data and 'access_token' in request.COOKIES:
            data['access_token'] = request.COOKIES['access_token']
        
        print("COOKIES:", request.COOKIES)
        
        serializer = SignOutSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            
            # Create response
            response = success(data=[], message="Logout successful.", status_code=status.HTTP_200_OK)
            
            # Clear cookies for web clients
            is_web = getattr(request, 'is_web_client', True)
            if is_web or 'access_token' in request.COOKIES:
                from .utils import clear_auth_cookies
                clear_auth_cookies(response)
            
            return response
        return error(message="Logout failed.", status_code=status.HTTP_400_BAD_REQUEST, errors=serializer.errors)


class ChangePasswordView(APIView):
    
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieJWTAuthentication]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return success(data=[], message="Password change successfully.", status_code=status.HTTP_200_OK)
        raise ValidationError(serializer.errors)

class SendOTPView(APIView):
    permission_classes = []

    def post(self, request):
        serializer = SendOTPSerializer(data=request.data)
        if serializer.is_valid():
            return success(data=[], message="OTP send to mail successfully.", status_code=status.HTTP_200_OK)
        errors = serializer.errors
        if "email" in errors:
            errors["error"] = errors.pop("email")
        raise ValidationError(errors)

class ResendOTPView(APIView):
    permission_classes = []

    def post(self, request):
        serializer = ResendOTPSerializer(data=request.data)
        if serializer.is_valid():
            return success(data=[], message="OTP send to mail successfully.", status_code=status.HTTP_200_OK)
        errors = serializer.errors
        if "email" in errors:
            errors["error"] = errors.pop("email")
        raise ValidationError(errors)

class VerifyOTPView(APIView):
    permission_classes = []

    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return success(data=[], message="OTP verify is successfully.", status_code=status.HTTP_200_OK)
        return error(message="OTP verify is failed.", status_code=status.HTTP_400_BAD_REQUEST, errors=serializer.errors)


class ResetPasswordView(APIView):
    permission_classes = []

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return success(data=[], message="Password reset successfully.", status_code=status.HTTP_200_OK)
        errors = serializer.errors
        if "non_field_errors" in errors:
            errors["error"] = errors.pop("non_field_errors")
        return error(message="Password reset failed.", status_code=status.HTTP_400_BAD_REQUEST, errors=errors)


class CookieTokenRefreshView(TokenRefreshView):
    """
    Hybrid Token Refresh View
    
    Supports both Web and Mobile clients:
    - Web: Reads refresh token from HttpOnly cookie, returns new tokens in cookies
    - Mobile: Reads refresh token from request body, returns new tokens in response body
    """
    
    def post(self, request, *args, **kwargs):
        # Inject refresh token from cookie into data if not present (for web clients)
        data = request.data.copy()
        if 'refresh' not in data and 'refresh_token' in request.COOKIES:
            data['refresh'] = request.COOKIES['refresh_token']
        
        serializer = self.get_serializer(data=data)

        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as e:
            raise InvalidToken(e.args[0])

        token_data = serializer.validated_data
        
        # Use hybrid response utility
        from .utils import create_hybrid_refresh_response
        
        tokens = {
            'access': token_data['access'],
            'refresh': token_data.get('refresh')  # May not exist if rotation is disabled
        }
        
        response = create_hybrid_refresh_response(
            tokens=tokens,
            request=request,
            message="Token refreshed successfully.",
            status_code=status.HTTP_200_OK
        )
        
        return response


class CookieTokenVerifyView(TokenVerifyView):

    
    def post(self, request, *args, **kwargs):

        data = request.data.copy()
        
        # Get token from request or cookie
        token = data.get('token') or request.COOKIES.get('access_token')
        if not token:
            return error(message="No token provided.", errors={}, status_code=status.HTTP_400_BAD_REQUEST)
        
        data['token'] = token
        
        # Validate token
        serializer = self.get_serializer(data=data)
        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as e:
            raise InvalidToken(e.args[0])
        
        # Get user from token
        jwt_auth = JWTAuthentication()
        validated_token = jwt_auth.get_validated_token(token)
        user = jwt_auth.get_user(validated_token)
        
        user_info = {
            'id': user.id,
            'email': user.email,
            'role': getattr(user, 'role', None),
        }
        
        return success(data=user_info, message="Token is valid.", status_code=status.HTTP_200_OK)






class UpdataProfileAvatarView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieJWTAuthentication]

    def post(self, request):
        user = request.user
        
        serializer = UpdataProfileAvatarSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return success(data=serializer.data, message="Profile avatar update successfully.", status_code=status.HTTP_200_OK)
        return error(message="Profile avatar update failed.", status_code=status.HTTP_400_BAD_REQUEST, errors=serializer.errors)




class AddNichesAndStageNamesView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieJWTAuthentication]

    def post(self, request):
        user = request.user
        
        niches = request.data.get('niches', [])
        stage_names = request.data.get('stage_names', [])
        
        
        # Add niches
        for niche in niches:
            Niche.objects.get_or_create(customer=user, name=niche)
        
        # Add stage names
        for stage_name in stage_names:
            StageName.objects.get_or_create(customer=user, name=stage_name)
        
        return success(data=[], message="Customer niches and stage names added successfully.", status_code=status.HTTP_200_OK)
    
class AddSocialAccountsView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieJWTAuthentication]

    def post(self, request):
        user = request.user
        accounts = request.data.get("accounts", [])  
        
        if not accounts or not isinstance(accounts, list):
            return error(message="Invalid accounts data.", status_code=status.HTTP_400_BAD_REQUEST)

        created_accounts = []
        for account in accounts:
            platform = account.get("platform")
            username = account.get("username")

            if not platform or not username:
                continue  # skip invalid entries

            obj, created = ConnectedSocialAccount.objects.get_or_create(
                customer=user,
                platform=platform,
                username=username
            )
            created_accounts.append({"platform": obj.platform, "username": obj.username})

        return success(data=created_accounts, message="Social accounts added successfully.", status_code=status.HTTP_200_OK)