import os
import django

# Set Django settings module FIRST
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')

# Setup Django BEFORE importing anything else
django.setup()

# Now import Django and Channels components
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from apps.chat.routing import websocket_urlpatterns

# Get the Django ASGI application
django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(
            websocket_urlpatterns
        )
    ),
})