import requests
from django.core.files.base import ContentFile
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from apps.user.models import User, UserProfile
from apps.utils.helpers import success,error
from uuid import uuid4

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

        if not email:
            return error("Email not available in Google user info", status_code=status.HTTP_400_BAD_REQUEST)

        # Check if the user exists, if not create one.
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            user = User.objects.create_user(
                email=email,
                password="passworasldfjadslfh@#@32"
            )
            if picture:
                image_response = requests.get(picture)
                if image_response.status_code == 200:
                    file_name = f"profile_{uuid4().hex}.jpg"  
                    if hasattr(user, 'avatar'):
                        user.avatar.save(file_name, ContentFile(image_response.content))


            UserProfile.objects.create(
                user=user,
                first_name=given_name,
                last_name=family_name
            )
           
        from apps.user.serializers import CustomRefreshToken
        from apps.user.utils import get_client_ip
        ip_address = get_client_ip(request)
        
        refresh = CustomRefreshToken.for_user(user, ip_address=ip_address)
        
        response = success({
            'user': {
                'id': user.id,
                'email': user.email,
                'role': user.role,
                 # Add other user fields as needed
            }
        }, message="Google login successful.")
        
        response.set_cookie(
            key='refresh_token', 
            value=str(refresh), 
            httponly=True, 
            secure=False, 
            samesite='Lax'
        )
        response.set_cookie(
            key='access_token', 
            value=str(refresh.access_token), 
            httponly=True, 
            secure=False, 
            samesite='Lax'
        )
        return response