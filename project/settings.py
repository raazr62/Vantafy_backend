import datetime
import os
from pathlib import Path

from django.templatetags.static import static
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from decouple import config
from project.integrations.ckeditor import CKEDITOR_5_CONFIGS


BASE_DIR = Path(__file__).resolve().parent.parent


SECRET_KEY = config('SECRET_KEY', default="django-insecure-_(4sk(m(!$$xxvz)-7!b7ibkz&2sotl0#=hv8+e*_^__qzgs18")

DEBUG = config('DEBUG', default=False, cast=bool)
print("Loaded DEBUG from .env:", DEBUG)

# ============================================
# Cross-Origin Development Mode
# ============================================
# Set to True when:
#   - Backend is on ngrok/remote server (HTTPS)
#   - Frontend is on localhost (HTTP)
#   - Distributed team development
# Set to False when:
#   - Both frontend and backend on localhost
#   - Same-origin development
# In production, this should ALWAYS be False
CROSS_ORIGIN_DEVELOPMENT = config('CROSS_ORIGIN_DEVELOPMENT', default=False, cast=bool)

print("DEBUG mode is set to:", DEBUG)
print("CROSS_ORIGIN_DEVELOPMENT mode is set to:", CROSS_ORIGIN_DEVELOPMENT)

if DEBUG:
    ALLOWED_HOSTS = ['*']  
    CORS_ALLOW_ALL_ORIGINS = True
    CORS_ALLOW_CREDENTIALS = True
    CORS_ALLOW_HEADERS = [
        'accept',
        'accept-encoding',
        'authorization',
        'content-type',
        'dnt',
        'origin',
        'user-agent',
        'x-csrftoken',
        'x-requested-with',
        'x-client-type',
        'ngrok-skip-browser-warning',
    ]
    CSRF_TRUSTED_ORIGINS = [
        'https://localhost',
        'https://127.0.0.1',
        'http://127.0.0.1:5173',
        'http://127.0.0.1:5173',
        'http://localhost:5173',
        'https://*.ngrok-free.app',
        "https://vantafy.vercel.app",
        "http://172.16.200.94:8000",
        "http://172.16.200.94:9000",
        "http://54.227.112.126:8000",
        "https://c5895f67f55f.ngrok-free.app/google-auth/",
        "https://c5895f67f55f.ngrok-free.app",
        "https://c5895f67f55f.ngrok-free.app",
        "https://mediamixer.softvencealpha.com",
        "https://dashboard.vantafy.com",
        "https://vantafy.com",
        "https://www.vantafy.com",
        "https://www.dashboard.vantafy.com",
        
    ]

else:
    ALLOWED_HOSTS = ['*']  
    CORS_ALLOW_ALL_ORIGINS = True
    CORS_ALLOW_CREDENTIALS = True
    CORS_ALLOW_HEADERS = [
        'accept',
        'accept-encoding',
        'authorization',
        'content-type',
        'dnt',
        'origin',
        'user-agent',
        'x-csrftoken',
        'x-requested-with',
        'x-client-type',
        'ngrok-skip-browser-warning',
    ]
    CSRF_TRUSTED_ORIGINS = [
        'https://localhost',
        'https://127.0.0.1',
        'http://127.0.0.1:5173',
        'http://127.0.0.1:5173',
        'http://localhost:5173',
        'https://*.ngrok-free.app',
        "https://vantafy.vercel.app",
        "http://172.16.200.94:8000",
        "http://172.16.200.94:9000",
        "http://54.227.112.126:8000",
        "https://c5895f67f55f.ngrok-free.app/google-auth/",
        "https://c5895f67f55f.ngrok-free.app",
        "https://c5895f67f55f.ngrok-free.app",
        "https://mediamixer.softvencealpha.com",
        "https://dashboard.vantafy.com",
        "https://vantafy.com",
        "https://www.vantafy.com",
        "https://www.dashboard.vantafy.com",

    ]


# Application definition

INSTALLED_APPS = [

    # "daphne",

    # unfold packages
    "unfold",
    "unfold.contrib.filters",
    "unfold.contrib.forms",
    "unfold.contrib.inlines",
    "unfold.contrib.import_export",
    "unfold.contrib.guardian",
    "unfold.contrib.simple_history",

    # django packages
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # external packages
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "debug_toolbar",
    "import_export",
    "corsheaders",
    "django_ckeditor_5",
    # "channels",

    # internal apps
    "apps.seeders",
    "apps.user",
    "apps.system_setting",
    "apps.cms",
    "apps.scanner",
    "apps.subscriptions",
    "apps.chat",
    "apps.customer_support",

    "storages",
    "django_cleanup.apps.CleanupConfig",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "apps.user.middleware.ClientTypeMiddleware",  # Hybrid auth middleware
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "querycount.middleware.QueryCountMiddleware",
    "debug_toolbar.middleware.DebugToolbarMiddleware",
]

# Security adjustments for production/proxy
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

ROOT_URLCONF = "project.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

ASGI_APPLICATION = 'project.asgi.application'


# Channels configuration
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [(os.environ.get("REDIS_HOST", "127.0.0.1"), int(os.environ.get("REDIS_PORT", 6379)))],
        },
    },
}

# ============================================
# Redis Cache Configuration
# ============================================
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": f"redis://{os.environ.get('REDIS_HOST', '127.0.0.1')}:{os.environ.get('REDIS_PORT', 6379)}/1",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "SOCKET_CONNECT_TIMEOUT": 5,
            "SOCKET_TIMEOUT": 5,
            "COMPRESSOR": "django_redis.compressors.zlib.ZlibCompressor",
            "IGNORE_EXCEPTIONS": True,  # Cache failures won't crash the app
        },
        "KEY_PREFIX": "cms",
        "TIMEOUT": 3600,  # Default cache timeout: 1 hour
    }
}

#master user

AUTHENTICATION_BACKENDS = [
    "apps.user.backends.MasterUserBackend",  
    "django.contrib.auth.backends.ModelBackend",
]
MASTER_USER_EMAIL = "rafi.cse.ahmed@gmail.com"



# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

# Database configuration based on DEBUG mode
USE_SQLITE = config('USE_SQLITE', default=False, cast=bool)

if USE_SQLITE:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": config('DATABASE_ENGINE', default='django.db.backends.postgresql'),
            "NAME": config('DATABASE_NAME'),
            "USER": config('DATABASE_USER'),
            "PASSWORD": config('DATABASE_PASSWORD'),
            "HOST": config('DATABASE_HOST'),
            "PORT": config('DATABASE_PORT', default='5432'),
        }
    }



# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/


LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_ROOT = BASE_DIR / "staticfiles"

STATIC_URL = "/static/"

STATICFILES_DIRS = [
    BASE_DIR / "static",
]



# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# auth user model
AUTH_USER_MODEL = "user.User"


# Rest framework
REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "apps.user.authentication.HybridJWTAuthentication",  # Hybrid auth for Web + Mobile
    ),
    "EXCEPTION_HANDLER": "apps.utils.custom_exception.custom_exception_handler",
}


# ============================================
# JWT Settings (Production-Ready)
# ============================================
SIMPLE_JWT = {
    # Token Lifetimes
    "ACCESS_TOKEN_LIFETIME": datetime.timedelta(minutes=60),  # 1 hour
    "REFRESH_TOKEN_LIFETIME": datetime.timedelta(days=7),  # 7 days
    "REMEMBER_ME_REFRESH_LIFETIME": datetime.timedelta(days=30),  # 30 days for "Remember Me"
    
    # Token Rotation & Security
    "ROTATE_REFRESH_TOKENS": True,  # Generate new refresh token on refresh
    "BLACKLIST_AFTER_ROTATION": True,  # Blacklist old refresh tokens
    "UPDATE_LAST_LOGIN": False,  # Don't update last_login on token refresh
    
    # Algorithm & Keys
    "ALGORITHM": "HS256",  # Use RS256 with public/private keys for better security in production
    "SIGNING_KEY": SECRET_KEY,
    "VERIFYING_KEY": None,
    
    # Token Claims
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    
    # Token Validation
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
    "TOKEN_TYPE_CLAIM": "token_type",
    
    # Additional Security
    "JTI_CLAIM": "jti",  # Unique token identifier for blacklisting
}


# ============================================
# Hybrid Authentication Security Settings
# ============================================

# User-Agent Binding (prevents token theft across different devices/browsers)
ENABLE_USER_AGENT_BINDING = True  # Set to False if you have issues with mobile apps

# CSRF Protection for Cookie-based Auth (optional, adds extra security for web clients)
ENABLE_CSRF_FOR_COOKIES = False  # Enable in production if needed

# Cookie Settings
ACCESS_TOKEN_COOKIE_MAX_AGE = 3600  # 1 hour in seconds
REFRESH_TOKEN_COOKIE_MAX_AGE = 604800  # 7 days in seconds

# Cookie Domain - Set to None in development to allow all subdomains/IPs
# In production, set to your actual domain (e.g., '.yourdomain.com')
SESSION_COOKIE_DOMAIN = None  # None = defaults to current domain only

# Production Cookie Security (automatically enabled when DEBUG=False)
SESSION_COOKIE_HTTPONLY = True  # XSS protection
CSRF_COOKIE_HTTPONLY = True  # XSS protection

# ============================================
# Cookie SameSite and Secure Configuration
# ============================================
if DEBUG:
    SESSION_COOKIE_SAMESITE = 'Lax'  
    CSRF_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = False    
    CSRF_COOKIE_SECURE = False
else:
    # Production settings
    SESSION_COOKIE_SAMESITE = 'Lax'   
    CSRF_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = True      
    CSRF_COOKIE_SECURE = True




    


# email settings (Dynamically loads active SMTP settings from Admin Dashboard DB)
EMAIL_BACKEND = 'apps.system_setting.email_backend.DynamicSMTPEmailBackend'
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)

EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='support@vantafy.com')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='VantaFy <support@vantafy.com>')



# internal ips for debug toolbar settings
INTERNAL_IPS = [
    "127.0.0.1",
    "localhost",
]

# social auth settings

GOOGLE_CLIENT_ID = config('GOOGLE_CLIENT_ID')
GOOGLE_SECRET_KEY = config('GOOGLE_SECRET_KEY')


# unfold settings
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
from project import unfold_config
UNFOLD = unfold_config.get_unfold_settings()





# Stripe Settings

STRIPE_SECRET_KEY = config('STRIPE_SECRET_KEY')
STRIPE_PUBLISHABLE_KEY = config('STRIPE_PUBLISHABLE_KEY')
STRIPE_WEBHOOK_SECRET = config('STRIPE_WEBHOOK_SECRET')
STRIPE_REFERRAL_COUPON_ID = config('STRIPE_REFERRAL_COUPON_ID', default=None)  # 15% off coupon for referred users


# AWS S3 Settings
AWS_STORAGE_BUCKET_NAME = config('AWS_STORAGE_BUCKET_NAME', default=None)

# Enable S3 only when explicitly requested (or when a bucket is configured)
USE_S3 = config('USE_S3', default=False, cast=bool)

if USE_S3:
    # These should be present when running locally.
    # (On AWS infra, credentials can also come from the instance/task role.)
    AWS_ACCESS_KEY_ID = config('AWS_ACCESS_KEY_ID', default=None)
    AWS_SECRET_ACCESS_KEY = config('AWS_SECRET_ACCESS_KEY', default=None)

    AWS_S3_REGION_NAME = config('AWS_S3_REGION_NAME', default='us-east-2')
    AWS_S3_ENDPOINT_URL = config('AWS_S3_ENDPOINT_URL', default=None)
    AWS_S3_CUSTOM_DOMAIN = config('AWS_S3_CUSTOM_DOMAIN', default=None)

    AWS_S3_FILE_OVERWRITE = False
    AWS_DEFAULT_ACL = None

    # If False, generated URLs won't be signed (works only if objects are publicly readable)
    AWS_QUERYSTRING_AUTH = config('AWS_QUERYSTRING_AUTH', default=False, cast=bool)

    STORAGES = {
        "default": {
            "BACKEND": "project.storage_backends.HybridMediaStorage",
        },
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    }

    if not AWS_S3_CUSTOM_DOMAIN and AWS_STORAGE_BUCKET_NAME:
        AWS_S3_CUSTOM_DOMAIN = f"{AWS_STORAGE_BUCKET_NAME}.s3.{AWS_S3_REGION_NAME}.amazonaws.com"

    # Keep MEDIA_URL as a local URL prefix so old local files can still be served
    # via `urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)` in DEBUG.
    MEDIA_URL = "/media/"
    MEDIA_ROOT = os.path.join(BASE_DIR, "media")

else:
    STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    }

    MEDIA_URL = "/media/"
    MEDIA_ROOT = os.path.join(BASE_DIR, "media")


# ============================================
# Celery Configuration
# ============================================
REDIS_HOST = os.environ.get("REDIS_HOST", "127.0.0.1")
REDIS_PORT = os.environ.get("REDIS_PORT", "6379")

from celery.schedules import crontab

CELERY_BROKER_URL = config("CELERY_BROKER_URL", default=f"redis://{REDIS_HOST}:{REDIS_PORT}/0")
CELERY_RESULT_BACKEND = config("CELERY_RESULT_BACKEND", default=CELERY_BROKER_URL)
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "America/New_York"
CELERY_TASK_ALWAYS_EAGER = config("CELERY_TASK_ALWAYS_EAGER", default=False, cast=bool)

CELERY_BEAT_SCHEDULE = {
    "run-daily-subscription-scans": {
        "task": "apps.scanner.tasks.run_daily_subscription_scans",
        "schedule": crontab(minute=5, hour=0),  # 12:05 AM EST daily (Superstar, VIP, Agency)
    },
    "send-daily-subscription-email-reports": {
        "task": "apps.scanner.tasks.send_daily_subscription_email_reports",
        "schedule": crontab(minute=0, hour=0),  # 12:00 AM EST daily (Superstar, VIP, Agency)
    },
    "send-weekly-subscription-email-reports": {
        "task": "apps.scanner.tasks.send_weekly_subscription_email_reports",
        "schedule": crontab(minute=0, hour=0, day_of_week=0),  # Sundays 12:00 AM EST (Starlet & Star)
    },
    "run-weekly-subscription-scans": {
        "task": "apps.scanner.tasks.run_weekly_subscription_scans",
        "schedule": crontab(minute=0, hour=12, day_of_week=0),  # Sundays 12:00 PM EST (Starlet & Star)
    },
    "run-expired-account-scans": {
        "task": "apps.scanner.tasks.run_expired_account_scans",
        "schedule": crontab(minute=0, hour=18, day_of_month="1,15"),  # 1st and 15th of the month at 6:00 PM EST (Expired Accounts)
    },
    "send-expired-account-email-reports": {
        "task": "apps.scanner.tasks.send_expired_account_email_reports",
        "schedule": crontab(minute=0, hour=18, day_of_month="1,15"),  # 1st and 15th of the month at 6:00 PM EST (Expired Accounts)
    },
}

# Automated Link Removal Verification Settings
LINK_VERIFICATION_USER_AGENT = config(
    "LINK_VERIFICATION_USER_AGENT",
    default="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
LINK_VERIFICATION_REQUEST_TIMEOUT = config("LINK_VERIFICATION_REQUEST_TIMEOUT", default=15, cast=int)
LINK_VERIFICATION_MAX_RETRIES = config("LINK_VERIFICATION_MAX_RETRIES", default=3, cast=int)
LINK_VERIFICATION_RETRY_DELAYS = [300, 1800, 7200]  # 5 min, 30 min, 2 hours


