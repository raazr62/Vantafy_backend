import requests
import secrets
from uuid import uuid4

from django.core.files.base import ContentFile
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import AllowAny
from apps.subscriptions.models import Subscription
from apps.user.models import User
from apps.utils.helpers import error
from apps.user.serializers import CustomRefreshToken
from apps.user.utils import get_user_agent_hash, create_hybrid_auth_response


class GoogleAuthView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):

        access_token = request.data.get('access_token')
        if not access_token:
            return error("Access token is required", status_code=status.HTTP_400_BAD_REQUEST)

        user_info_url = "https://www.googleapis.com/oauth2/v3/userinfo"
        response = requests.get(
            user_info_url,
            headers={'Authorization': f'Bearer {access_token}'}
        )

        if response.status_code != 200:
            return error("Failed to fetch user info from Google", status_code=status.HTTP_400_BAD_REQUEST)

        user_info = response.json()

        email = user_info.get('email')
        name = user_info.get('name')
        given_name = user_info.get('given_name')
        family_name = user_info.get('family_name')
        picture = user_info.get('picture')

        full_name = name or f"{given_name or ''} {family_name or ''}".strip()

        if not email:
            return error("Email not available in Google user info", status_code=status.HTTP_400_BAD_REQUEST)

        #  CHECK USER
        
        user = User.objects.filter(email=email).first()

        if not user:
            role = request.data.get('role')
            if role not in [User.Roles.CUSTOMER, User.Roles.AGENCY]:
                return error("Invalid role specified", status_code=status.HTTP_400_BAD_REQUEST)

            random_password = secrets.token_urlsafe(32)
            user = User.objects.create_user(
                email=email,
                full_name=full_name,
                password=random_password,
                role=role,
                term_and_condition_accepted=True
            )

            #  SAVE PROFILE IMAGE
            if picture:
                image_response = requests.get(picture)
                if image_response.status_code == 200 and hasattr(user, 'avatar'):
                    file_name = f"profile_{uuid4().hex}.jpg"
                    user.avatar.save(
                        file_name,
                        ContentFile(image_response.content),
                        save=True
                    )

        #  USER AGENT HASH
        user_agent_hash = get_user_agent_hash(request)

        #  TOKENS
        refresh = CustomRefreshToken.for_user(
            user,
            user_agent_hash=user_agent_hash
        )

        tokens = {
            'access': str(refresh.access_token),
            'refresh': str(refresh)
        }

        has_subscription = Subscription.objects.filter(user=user,status='active',).exists()        

        user_data = {
            'id': user.id,
            'email': user.email,
            'full_name': user.full_name,
            'role': user.role,
            'has_subscription': has_subscription,
        }

        return create_hybrid_auth_response(
            data=user_data,
            tokens=tokens,
            request=request,
            message="Google login successful.",
            status_code=status.HTTP_200_OK
        )
