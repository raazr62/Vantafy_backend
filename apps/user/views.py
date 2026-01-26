from datetime import timezone
from email.mime import message
import json
import os
from django.conf import settings
from rest_framework.exceptions import ValidationError
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from apps.user.models import Niche
from .authentication import CookieJWTAuthentication
from .models import AgencyMemberList, AgencyMemberNiches, AgencyMemberSocialAccounts, AgencyMemberStageNames, Niche, StageName, User
from .models import ConnectedSocialAccount
from apps.subscriptions.models import Subscription
from .utils import clear_auth_cookies
# from names_dataset import NameDataset



# Use hybrid response utility
from .utils import create_hybrid_auth_response

from .serializers import (
    SignUpSerializer,
    SignInSerializer,
    SignOutSerializer,
    ChangePasswordSerializer,
    SendOTPSerializer,
    ResendOTPSerializer,
    StageNameSerializer,
    VerifyOTPSerializer,
    ResetPasswordSerializer,
    UpdataProfileAvatarSerializer,
    UpdateProfileSerializer,
    NichesSerializer,
    AgencyMemberListSerializer
)

from apps.utils.helpers import success, error


# Create your views here.
class SignUpView(APIView):
    permission_classes = []

    def post(self, request):

        role = request.data.get('role')
        if role not in ['customer', 'agency']:
            return error(message="Invalid role provided.", status_code=status.HTTP_400_BAD_REQUEST)

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
            return error(message="No token provided.", errors={}, status_code=status.HTTP_401_UNAUTHORIZED)
        
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

        has_subscription = Subscription.objects.filter(user=user,status='active',).exists()        
    
        user_info = {
            'id': user.id,
            'email': user.email,
            'role': getattr(user, 'role', None),
            'has_subscription': has_subscription,
            'is_google_login': user.is_google_login,
        }
        
        return success(data=user_info, message="Token is valid.", status_code=status.HTTP_200_OK)






class UpdataProfileAvatarView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieJWTAuthentication]

    def post(self, request):
        user = request.user
        cookies = request.COOKIES
        print("COOKIES IN AVATAR UPDATE VIEW:", cookies)
        
        serializer = UpdataProfileAvatarSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return success(data=serializer.data, message="Profile avatar update successfully.", status_code=status.HTTP_200_OK)
        return error(message="Profile avatar update failed.", status_code=status.HTTP_400_BAD_REQUEST, errors=serializer.errors)


class ProfileUpdateAPIView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieJWTAuthentication]

    def put(self, request):
        user = request.user
        
        serializer = UpdateProfileSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return success(data=serializer.data, message="Profile updated successfully.", status_code=status.HTTP_200_OK)
        return error(message="Profile update failed.", status_code=status.HTTP_400_BAD_REQUEST, errors=serializer.errors)
    
class MyProfileView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieJWTAuthentication]

    def get(self, request):
        user = request.user
        
        has_subscription = Subscription.objects.filter(user=user,status='active',).exists()        
        
        user_data = {
            'id': user.id,
            'email': user.email,
            'full_name': user.full_name,
            'country': user.country,
            'time_zone': user.time_zone,
            'avatar': user.avatar.url if user.avatar else None,
            'role': user.role,
            'has_subscription': has_subscription,
        }
        
        return success(data=user_data, message="User profile fetched successfully.", status_code=status.HTTP_200_OK)
    
class MyNichesView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieJWTAuthentication]

    def get(self, request):
        user = request.user
        
        niches = Niche.objects.filter(customer=user)
        
        data = NichesSerializer(niches, many=True).data
        
        return success(data=data, message="User niches and stage names fetched successfully.", status_code=status.HTTP_200_OK)
    
class CreateOrDeleteNichesView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieJWTAuthentication]

    def post(self, request):
        user = request.user
        name = request.data.get('name')

        if not name:
            return error(message="Niche name is required.", status_code=status.HTTP_400_BAD_REQUEST)
        
        niche = Niche.objects.filter(customer=user, name=name).first()

        if niche:
            niche.delete()
            return success(data={"name": name, "deleted": True}, message="Niche deleted successfully.", status_code=status.HTTP_200_OK)
        
        else:
            niche = Niche.objects.create(customer=user, name=name)
            return success(data={"niche_id": niche.id, "name": niche.name, "created": True}, message="Niche created successfully.", status_code=status.HTTP_201_CREATED)


class AddStageNameView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieJWTAuthentication]

    def post(self, request):
        user = request.user
        raw_name = request.data.get('name')

        if not raw_name:
            return error(message="Stage name is required.", status_code=status.HTTP_400_BAD_REQUEST)

        name = str(raw_name).strip()

        if not name:
            return error(message="Stage name is required.", status_code=status.HTTP_400_BAD_REQUEST)

        try:
            file_path = os.path.join(settings.BASE_DIR, 'common-names', 'common-names.json')
            with open(file_path, 'r') as file:
                payload = json.load(file)

            print("COMMON NAMES PAYLOAD LOADED:", payload)
            # Extract first_name values from the list of dicts
            common_names_set = {
                str(item.get("first_name", "")).strip().lower()
                for item in payload
                if isinstance(item, dict) and item.get("first_name")
            }
        except (FileNotFoundError, json.JSONDecodeError, Exception):
            common_names_set = set()

        is_common = name.lower() in common_names_set

        stage_name, created = StageName.objects.get_or_create(
            customer=user,
            name=name,
            is_common=is_common
        )

        return success(
            data={
                "stage_name_id": stage_name.id,
                "name": stage_name.name,
                "is_common": stage_name.is_common,
                "created": created
            },
            message="Stage name created successfully." if created else "Stage name already exists.",
            status_code=status.HTTP_200_OK
        )
    

class MyStageNamesView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieJWTAuthentication]

    def get(self, request):
        user = request.user
        
        stage_names = StageName.objects.filter(customer=user)
        stage_name_data = [{"id": stage_name.id, "name": stage_name.name, "is_common": stage_name.is_common} for stage_name in stage_names]

        return success(
            data=stage_name_data,
            message="Stage names fetched successfully.",
            status_code=status.HTTP_200_OK
        )


class UpdateStageNameApi(APIView):

    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieJWTAuthentication]

    def put(self, request, stage_name_id):
        user = request.user

        try:
            stage_name = StageName.objects.get(id=stage_name_id, customer=user)
        except StageName.DoesNotExist:
            return error(message="Stage name not found.", status_code=status.HTTP_404_NOT_FOUND)
        
        name = request.data.get("name")
        if not name:
            return error(message="Stage name is required.", status_code=status.HTTP_400_BAD_REQUEST)
        
        stage_name.name = name
        stage_name.save()

        return success(
            data={
                "stage_name_id": stage_name.id,
                "name": stage_name.name
            },
            message="Stage name updated successfully.",
            status_code=status.HTTP_200_OK
        )
    


class DeleteStageNameView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieJWTAuthentication]

    def delete(self, request, stage_name_id):
        user = request.user

        try:
            stage_name = StageName.objects.get(id=stage_name_id, customer=user)
        except StageName.DoesNotExist:
            return error(message="Stage name not found.", status_code=status.HTTP_404_NOT_FOUND)
        
        stage_name.delete()
        return success(data=[], message="Stage name deleted successfully.", status_code=status.HTTP_200_OK)



    

    
class GetNichesView(APIView):
    permission_classes = []

    def get(self, request):
    
        niches = Niche.objects.all()

        if not niches.exists():
            return error(message="No niches found.", errors=None, code=200)
        
        serializer = NichesSerializer(niches, many=True)
        return success(data=serializer.data,message="Customer niches fetched successfully.", status_code=status.HTTP_200_OK)

        
        

class AddNichesAndStageNamesView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieJWTAuthentication]

    def post(self, request):
        user = request.user

        niches = request.data.get('niches', [])
        stage_names = request.data.get('stageNames', [])

        # Convert string arrays to object arrays
        niche_data = [{"name": n} for n in niches]
        stage_name_data = [{"name": s} for s in stage_names]

        niche_serializer = NichesSerializer(data=niche_data, many=True)
        stage_name_serializer = StageNameSerializer(data=stage_name_data, many=True)

        if not niche_serializer.is_valid():
            return error(
                message="Invalid niches data.",
                status_code=status.HTTP_400_BAD_REQUEST,
                errors=niche_serializer.errors
            )

        if not stage_name_serializer.is_valid():
            return error(
                message="Invalid stage names data.",
                status_code=status.HTTP_400_BAD_REQUEST,
                errors=stage_name_serializer.errors
            )

        niche_serializer.save(customer=user)
        stage_name_serializer.save(customer=user)

        return success(
            data=[],
            message="Customer niches and stage names added successfully.",
            status_code=status.HTTP_200_OK
        )
    
class AddSocialAccountsView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieJWTAuthentication]

    def post(self, request):
        user = request.user
        platform = request.data.get('platform')

        if not platform:
            return error(message="Platform is required.", status_code=status.HTTP_400_BAD_REQUEST)
        
        social_account, created = ConnectedSocialAccount.objects.get_or_create(customer=user, platform=platform)

        return success(
            data={
                "social_account_id": social_account.id,
                "platform": social_account.platform,
                "created": created
            },
            message="Social account added successfully." if created else "Social account already exists.",
            status_code=status.HTTP_200_OK
        )
        
class GetSocialAccountView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieJWTAuthentication]

    def get(self, request):
        user = request.user
        
        social_accounts = ConnectedSocialAccount.objects.filter(customer=user)
        social_account_data = [{"id": account.id, "platform": account.platform} for account in social_accounts]

        return success(
            data=social_account_data,
            message="Social accounts fetched successfully.",
            status_code=status.HTTP_200_OK
        )


    

class DeleteSocialAccountView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieJWTAuthentication]

    def delete(self, request, account_id):
        user = request.user

        try:
            social_account = ConnectedSocialAccount.objects.get(id=account_id, customer=user)
        except ConnectedSocialAccount.DoesNotExist:
            return error(message="Social account not found.", status_code=status.HTTP_404_NOT_FOUND)
        
        social_account.delete()

        return success(data=[], message="Social account deleted successfully.", status_code=status.HTTP_200_OK)
  
class AddAgencyMemberView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieJWTAuthentication]

    def post(self, request):
        agency = request.user
        if agency.role != User.Roles.AGENCY:
            return error(message="Only agency users can add agency members.", status_code=status.HTTP_403_FORBIDDEN)
        
        name = request.data.get('name')
        profile_image = request.FILES.get('profile_image')

        member = AgencyMemberList.objects.create(
            agency=agency,
            name=name,
            profile_image=profile_image
        )

        return success(data={"member_id": member.id}, message="Agency member added successfully.", status_code=status.HTTP_201_CREATED)
    
class AgencyMemberListView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieJWTAuthentication]

    def get(self, request):
        agency = request.user
        if agency.role != User.Roles.AGENCY:
            return error(message="Only agency users can view agency members.", status_code=status.HTTP_403_FORBIDDEN)
        
        members = AgencyMemberList.objects.filter(agency=agency)
        serializer = AgencyMemberListSerializer(members, many=True)
        return success(data=serializer.data, message="Agency members fetched successfully.", status_code=status.HTTP_200_OK)
    

class UpdateAgencyMemberDataView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieJWTAuthentication]

    def put(self, request, member_id):
        agency = request.user
        if agency.role != User.Roles.AGENCY:
            return error(message="Only agency users can update agency members.", status_code=status.HTTP_403_FORBIDDEN)
        
        try:
            member = AgencyMemberList.objects.get(id=member_id, agency=agency)
        except AgencyMemberList.DoesNotExist:
            return error(message="Agency member not found.", status_code=status.HTTP_404_NOT_FOUND)
        
        serializer = AgencyMemberListSerializer(member, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return success(data=serializer.data, message="Agency member updated successfully.", status_code=status.HTTP_200_OK)
        return error(message="Invalid data.", status_code=status.HTTP_400_BAD_REQUEST, errors=serializer.errors)
    
class DeleteAgencyMemberDataView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieJWTAuthentication]

    def delete(self, request, member_id):
        agency = request.user
        if agency.role != User.Roles.AGENCY:
            return error(message="Only agency users can delete agency members.", status_code=status.HTTP_403_FORBIDDEN)
        
        try:
            member = AgencyMemberList.objects.get(id=member_id, agency=agency)
        except AgencyMemberList.DoesNotExist:
            return error(message="Agency member not found.", status_code=status.HTTP_404_NOT_FOUND)
        
        member.delete()
        return success(data=[], message="Agency member deleted successfully.", status_code=status.HTTP_200_OK)
    


class CreateOrUpdateAgencyMemberNichesView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieJWTAuthentication]

    def post(self, request, member_id):
        agency = request.user

        if agency.role != User.Roles.AGENCY:
            return error(
                message="Only agency users can manage agency member niches.",
                status_code=status.HTTP_403_FORBIDDEN
            )

        try:
            member = AgencyMemberList.objects.get(id=member_id, agency=agency)
        except AgencyMemberList.DoesNotExist:
            return error(
                message="Agency member not found.",
                status_code=status.HTTP_404_NOT_FOUND
            )

        name = request.data.get("name")
        if not name:
            return error(
                message="Niche name is required.",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        niche = AgencyMemberNiches.objects.filter(
            agency_member=member,
            name=name
        ).first()

        if niche:
            niche.delete()
            return success(
                data={
                    "name": name,
                    "deleted": True
                },
                message="Agency member niche removed successfully.",
                status_code=status.HTTP_200_OK
            )

        niche = AgencyMemberNiches.objects.create(
            agency_member=member,
            name=name
        )

        return success(
            data={
                "niche_id": niche.id,
                "name": niche.name,
                "created": True
            },
            message="Agency member niche created successfully.",
            status_code=status.HTTP_201_CREATED
        )


class AgencyMemberNichesView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieJWTAuthentication]

    def get(self, request, member_id):
        agency = request.user

        if agency.role != User.Roles.AGENCY:
            return error(
                message="Only agency users can view agency member niches.",
                status_code=status.HTTP_403_FORBIDDEN
            )

        try:
            member = AgencyMemberList.objects.get(id=member_id, agency=agency)
        except AgencyMemberList.DoesNotExist:
            return error(
                message="Agency member not found.",
                status_code=status.HTTP_404_NOT_FOUND
            )

        niches = AgencyMemberNiches.objects.filter(agency_member=member)
        niche_data = [{"id": niche.id, "name": niche.name} for niche in niches]

        return success(
            data=niche_data,
            message="Agency member niches fetched successfully.",
            status_code=status.HTTP_200_OK
        )
    


class AddAgencyMemberStageNamesView(APIView):

    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieJWTAuthentication]

    def post(self, request, member_id):
        agency = request.user

        if agency.role != User.Roles.AGENCY:
            return error(
                message="Only agency users can manage agency member stage names.",
                status_code=status.HTTP_403_FORBIDDEN
            )

        try:
            member = AgencyMemberList.objects.get(id=member_id, agency=agency)
        except AgencyMemberList.DoesNotExist:
            return error(
                message="Agency member not found.",
                status_code=status.HTTP_404_NOT_FOUND
            )

        name = request.data.get("name")
        if not name:
            return error(
                message="Stage name is required.",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        stage_name, created = AgencyMemberStageNames.objects.get_or_create(
            agency_member=member,
            name=name
        )

        return success(
            data={
                "stage_name_id": stage_name.id,
                "name": stage_name.name,
                "created": created
            },
            message="Agency member stage name created successfully." if created else "Agency member stage name already exists.",
            status_code=status.HTTP_200_OK
        )
    
class UpdateAgencyMemberStageNamesView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieJWTAuthentication]

    def put(self, request, stage_name_id):
        agency = request.user

        if agency.role != User.Roles.AGENCY:
            return error(
                message="Only agency users can edit agency member stage names.",
                status_code=status.HTTP_403_FORBIDDEN
            )

        try:
            stage_name = AgencyMemberStageNames.objects.get(id=stage_name_id, agency_member__agency=agency)
        except AgencyMemberStageNames.DoesNotExist:
            return error(
                message="Agency member stage name not found.",
                status_code=status.HTTP_404_NOT_FOUND
            )
        name = request.data.get("name")
        if not name:
            return error(
                message="Stage name is required.",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        stage_name.name = name
        stage_name.save()

        return success(
            data={
                "stage_name_id": stage_name.id,
                "name": stage_name.name
            },
            message="Agency member stage name updated successfully.",
            status_code=status.HTTP_200_OK
        )
           
class GetAgencyMemberStageNamesView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieJWTAuthentication]

    def get(self, request, member_id):
        agency = request.user

        if agency.role != User.Roles.AGENCY:
            return error(
                message="Only agency users can view agency member stage names.",
                status_code=status.HTTP_403_FORBIDDEN
            )

        try:
            member = AgencyMemberList.objects.get(id=member_id, agency=agency)
        except AgencyMemberList.DoesNotExist:
            return error(
                message="Agency member not found.",
                status_code=status.HTTP_404_NOT_FOUND
            )

        stage_names = AgencyMemberStageNames.objects.filter(agency_member=member)
        stage_name_data = [{"id": stage_name.id, "name": stage_name.name} for stage_name in stage_names]

        return success(
            data=stage_name_data,
            message="Agency member stage names fetched successfully.",
            status_code=status.HTTP_200_OK
        )
    
class DeleteAgencyMemberStageNameView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieJWTAuthentication]

    def delete(self, request, stage_name_id):
        agency = request.user

        if agency.role != User.Roles.AGENCY:
            return error(
                message="Only agency users can delete agency member stage names.",
                status_code=status.HTTP_403_FORBIDDEN
            )

        try:
            stage_name = AgencyMemberStageNames.objects.get(id=stage_name_id, agency_member__agency=agency)
        except AgencyMemberStageNames.DoesNotExist:
            return error(
                message="Agency member stage name not found.",
                status_code=status.HTTP_404_NOT_FOUND
            )

        stage_name.delete()

        return success(
            data=[],
            message="Agency member stage name deleted successfully.",
            status_code=status.HTTP_200_OK
        )
    
class AddAgencyMemberSocialAccountsView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieJWTAuthentication]

    def post(self, request, member_id):
        agency = request.user

        if agency.role != User.Roles.AGENCY:
            return error(
                message="Only agency users can add social accounts for agency members.",
                status_code=status.HTTP_403_FORBIDDEN
            )

        try:
            member = AgencyMemberList.objects.get(id=member_id, agency=agency)
        except AgencyMemberList.DoesNotExist:
            return error(
                message="Agency member not found.",
                status_code=status.HTTP_404_NOT_FOUND
            )

        platform = request.data.get("platform")

        existing_accounts = AgencyMemberSocialAccounts.objects.filter(
            agency_member=member,
            platform=platform
        )
        
        if existing_accounts.exists():
            if existing_accounts.count() > 1:
                social_account = existing_accounts.latest('id')
                existing_accounts.exclude(id=social_account.id).delete()
                created = False
            else:
                social_account = existing_accounts.first()
                created = False
        else:
            social_account = AgencyMemberSocialAccounts.objects.create(
                agency_member=member,
                platform=platform
            )
            created = True

        return success(
            data={
                "platform": social_account.platform,
                "id": social_account.id,
                "created": created
            },
            message="Agency member social account added successfully.",
            status_code=status.HTTP_201_CREATED
        )
    

class GetAgencyMemberSocialAccountsView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieJWTAuthentication]

    def get(self, request, member_id):
        agency = request.user

        if agency.role != User.Roles.AGENCY:
            return error(
                message="Only agency users can view social accounts for agency members.",
                status_code=status.HTTP_403_FORBIDDEN
            )

        try:
            member = AgencyMemberList.objects.get(id=member_id, agency=agency)
        except AgencyMemberList.DoesNotExist:
            return error(
                message="Agency member not found.",
                status_code=status.HTTP_404_NOT_FOUND
            )

        social_accounts = AgencyMemberSocialAccounts.objects.filter(agency_member=member)
        account_data = [{"id": account.id, "platform": account.platform} for account in social_accounts]

        return success(
            data=account_data,
            message="Agency member social accounts fetched successfully.",
            status_code=status.HTTP_200_OK
        )
    
class DeleteAgencyMemberSocialAccountView(APIView):

    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieJWTAuthentication]

    def delete(self, request, account_id):
        agency = request.user

        if agency.role != User.Roles.AGENCY:
            return error(
                message="Only agency users can delete social accounts for agency members.",
                status_code=status.HTTP_403_FORBIDDEN
            )

        try:
            social_account = AgencyMemberSocialAccounts.objects.get(
                id=account_id,
                agency_member__agency=agency
            )
        except AgencyMemberSocialAccounts.DoesNotExist:
            return error(
                message="Agency member social account not found.",
                status_code=status.HTTP_404_NOT_FOUND
            )

        social_account.delete()

        return success(
            data=[],
            message="Agency member social account deleted successfully.",
            status_code=status.HTTP_200_OK
        )