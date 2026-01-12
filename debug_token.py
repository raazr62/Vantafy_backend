import os
import django
import sys

# Setup Django environment
sys.path.append('c:/projects/mediamixer_django')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from apps.user.models import User
from apps.user.serializers import CustomRefreshToken
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

def debug_token():
    try:
        # Create or get user
        user, created = User.objects.get_or_create(email='debug_test@test.com', defaults={'is_active': True})
        if created:
            user.set_password('password')
            user.save()
            
        print(f"User: {user.email}")
        
        # Generate Token (Simulate SignInSerializer)
        refresh = CustomRefreshToken.for_user(user)
        access_str = str(refresh.access_token)
        
        print(f"Generated Access Token: {access_str}")
        
        # Verify Token
        try:
            token = AccessToken(access_str)
            print("Access Token Verified Successfully!")
            print(f"Token Payload: {token.payload}")
        except Exception as e:
            print(f"Access Token Verification FAILED: {e}")
            
    except Exception as e:
        print(f"Script Error: {e}")

if __name__ == "__main__":
    debug_token()
