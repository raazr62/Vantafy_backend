# 🔒 Security Checklist for Production Deployment

## ✅ Pre-Production Checklist

### Django Settings

- [ ] **DEBUG = False** in production
- [ ] **SECRET_KEY** loaded from environment variable (not hardcoded)
- [ ] **ALLOWED_HOSTS** configured with your actual domains
- [ ] **CORS_ALLOWED_ORIGINS** set to specific domains (not `*`)
- [ ] **CORS_ALLOW_CREDENTIALS = True** for cookie support
- [ ] **CSRF_TRUSTED_ORIGINS** includes your frontend domains

### HTTPS & SSL

- [ ] **HTTPS enabled** on production server (Let's Encrypt recommended)
- [ ] **SESSION_COOKIE_SECURE = True** (HTTPS only cookies)
- [ ] **CSRF_COOKIE_SECURE = True** (HTTPS only cookies)
- [ ] **SECURE_SSL_REDIRECT = True** (redirect HTTP to HTTPS)
- [ ] **HSTS enabled** (`SECURE_HSTS_SECONDS = 31536000`)

### JWT Configuration

- [ ] **ACCESS_TOKEN_LIFETIME** appropriate (default: 1 hour)
- [ ] **REFRESH_TOKEN_LIFETIME** appropriate (default: 7 days)
- [ ] **ROTATE_REFRESH_TOKENS = True** (generate new on refresh)
- [ ] **BLACKLIST_AFTER_ROTATION = True** (invalidate old tokens)
- [ ] **Consider RS256 algorithm** with public/private keys for better security

### Cookie Security

- [ ] **HttpOnly = True** (prevents XSS attacks)
- [ ] **Secure = True** in production (HTTPS only)
- [ ] **SameSite = 'Lax' or 'Strict'** (prevents CSRF attacks)
- [ ] **Cookie max ages** configured appropriately

### Database

- [ ] **PostgreSQL** (or production database, not SQLite)
- [ ] **Database credentials** in environment variables
- [ ] **Database connection** uses SSL
- [ ] **Regular backups** configured
- [ ] **Index on token blacklist** for performance

### Authentication Security

- [ ] **ENABLE_USER_AGENT_BINDING = True** (unless causing issues)
- [ ] **Rate limiting** on auth endpoints
- [ ] **Strong password validation** enabled
- [ ] **Account lockout** after failed attempts (optional)
- [ ] **Email verification** for new accounts

### Headers & Security Middleware

- [ ] **X-Frame-Options** set (`X_FRAME_OPTIONS = 'DENY'`)
- [ ] **X-Content-Type-Options** enabled
- [ ] **XSS filter** enabled
- [ ] **Content Security Policy** configured
- [ ] **ClientTypeMiddleware** added to MIDDLEWARE

### API Security

- [ ] **Input validation** on all endpoints
- [ ] **Output sanitization** for user data
- [ ] **SQL injection** protection (Django ORM handles this)
- [ ] **CSRF protection** enabled
- [ ] **Request size limits** configured

### Monitoring & Logging

- [ ] **Error logging** configured (Sentry, etc.)
- [ ] **Access logging** enabled
- [ ] **Failed login attempts** logged
- [ ] **Security alerts** configured
- [ ] **Regular security audits** scheduled

### Token Management

- [ ] **Token blacklist cleanup** scheduled (weekly)
  ```bash
  python manage.py flushexpiredtokens
  ```
- [ ] **Expired tokens** automatically cleaned
- [ ] **Token rotation** working correctly
- [ ] **Token validation** tested

### Client Applications

#### Web Client
- [ ] **X-Client-Type: web** header sent
- [ ] **credentials: 'include'** in fetch/axios
- [ ] **Tokens NOT in localStorage** (cookies only)
- [ ] **CORS configured** correctly
- [ ] **HTTPS** used in production

#### Mobile Client
- [ ] **X-Client-Type: mobile** header sent
- [ ] **Tokens stored securely** (flutter_secure_storage, Keychain)
- [ ] **Authorization header** format correct
- [ ] **Token refresh** implemented
- [ ] **Logout clears tokens**

### Testing

- [ ] **Web client login** tested
- [ ] **Mobile client login** tested
- [ ] **Token refresh** tested (both clients)
- [ ] **Token expiration** tested
- [ ] **Logout** tested (both clients)
- [ ] **User-Agent binding** tested
- [ ] **CORS** tested from real domains
- [ ] **Rate limiting** tested
- [ ] **Security headers** verified

### Documentation

- [ ] **API documentation** up to date
- [ ] **Client examples** provided
- [ ] **Security policies** documented
- [ ] **Deployment guide** created
- [ ] **Troubleshooting guide** available

---

## 🚨 Critical Production Settings

### Minimum Required Settings

```python
# project/settings.py

import os
from decouple import config

# CRITICAL: Never commit these!
SECRET_KEY = config('SECRET_KEY')
DEBUG = False

# Allowed hosts
ALLOWED_HOSTS = ['yourdomain.com', 'api.yourdomain.com']

# HTTPS enforcement
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# HSTS
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# CORS
CORS_ALLOWED_ORIGINS = [
    'https://yourfrontend.com',
]
CORS_ALLOW_CREDENTIALS = True

# CSRF
CSRF_TRUSTED_ORIGINS = [
    'https://yourfrontend.com',
]

# Database - PostgreSQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DATABASE_NAME'),
        'USER': config('DATABASE_USER'),
        'PASSWORD': config('DATABASE_PASSWORD'),
        'HOST': config('DATABASE_HOST'),
        'PORT': config('DATABASE_PORT', default='5432'),
        'OPTIONS': {
            'sslmode': 'require',  # SSL connection
        },
    }
}

# JWT - Production settings
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': 'HS256',  # Or RS256 with keys
    'SIGNING_KEY': SECRET_KEY,
}

# Hybrid auth security
ENABLE_USER_AGENT_BINDING = True
ENABLE_CSRF_FOR_COOKIES = False
ACCESS_TOKEN_COOKIE_MAX_AGE = 3600
REFRESH_TOKEN_COOKIE_MAX_AGE = 604800
```

---

## 🔧 Environment Variables (.env)

Create a `.env` file (NEVER commit this):

```bash
# Django
SECRET_KEY=your-super-secret-key-here-generate-a-new-one
DEBUG=False

# Database
DATABASE_NAME=your_db_name
DATABASE_USER=your_db_user
DATABASE_PASSWORD=your_db_password
DATABASE_HOST=your_db_host
DATABASE_PORT=5432

# Email (if using email features)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-email-password

# Google OAuth (if using social auth)
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_SECRET_KEY=your-google-secret-key

# Sentry (optional, for error tracking)
SENTRY_DSN=your-sentry-dsn
```

---

## 🛡️ Security Best Practices

### 1. Password Security

```python
# settings.py
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]
```

### 2. Rate Limiting

Install django-ratelimit:
```bash
pip install django-ratelimit
```

Apply to auth views:
```python
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator

@method_decorator(ratelimit(key='ip', rate='5/m', method='POST'), name='dispatch')
class SignInView(APIView):
    # ... existing code
```

### 3. Account Lockout

Track failed login attempts in your SignInSerializer:
```python
# After 5 failed attempts, lock account for 15 minutes
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_DURATION = 900  # 15 minutes
```

### 4. Token Cleanup

Add to your cron or task scheduler:
```bash
# Run weekly
0 0 * * 0 /path/to/manage.py flushexpiredtokens
```

### 5. Security Headers Middleware

```python
# middleware.py
class SecurityHeadersMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        return response
```

---

## 🔍 Security Audit Commands

### Check for security issues:
```bash
python manage.py check --deploy
```

### Test for common vulnerabilities:
```bash
pip install bandit
bandit -r apps/
```

### Check dependencies for vulnerabilities:
```bash
pip install safety
safety check
```

---

## 📊 Monitoring Recommendations

### Application Monitoring
- **Sentry**: Error tracking and performance monitoring
- **New Relic**: APM and infrastructure monitoring
- **DataDog**: Full-stack observability

### Security Monitoring
- **CloudFlare**: DDoS protection and WAF
- **AWS GuardDuty**: Threat detection
- **Fail2Ban**: Intrusion prevention

### Log Aggregation
- **ELK Stack**: Elasticsearch, Logstash, Kibana
- **Splunk**: Enterprise log management
- **Papertrail**: Simple log management

---

## 🚀 Deployment Platforms

### Recommended Platforms
1. **AWS**: Full control, scalable
2. **DigitalOcean**: Simple, affordable
3. **Heroku**: Easy deployment, managed
4. **Railway**: Modern, simple
5. **Fly.io**: Edge deployment

### Deployment Checklist
- [ ] **HTTPS/SSL** certificate installed
- [ ] **Static files** served via CDN
- [ ] **Media files** stored in S3/similar
- [ ] **Database** backed up regularly
- [ ] **Environment variables** configured
- [ ] **Logs** being collected
- [ ] **Monitoring** active
- [ ] **Alerts** configured

---

## 📞 Incident Response

### If Security Breach Occurs:

1. **Immediate Actions**:
   - Rotate SECRET_KEY
   - Blacklist all tokens
   - Reset all user passwords
   - Lock affected accounts

2. **Investigation**:
   - Check logs for unauthorized access
   - Identify breach vector
   - Assess data exposure

3. **Communication**:
   - Notify affected users
   - Report to authorities if required
   - Document incident

4. **Prevention**:
   - Patch vulnerabilities
   - Update security measures
   - Improve monitoring

---

## ✅ Final Verification

Before going live, run through this final checklist:

```bash
# 1. Check deployment settings
python manage.py check --deploy

# 2. Test authentication
curl -X POST https://yourdomain.com/api/user/signin/ \
  -H "Content-Type: application/json" \
  -H "X-Client-Type: web" \
  -d '{"email": "test@example.com", "password": "test123"}'

# 3. Verify HTTPS
curl -I https://yourdomain.com

# 4. Check security headers
curl -I https://yourdomain.com | grep -E "(X-|Strict|Content-Security)"

# 5. Test CORS
curl -H "Origin: https://yourfrontend.com" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: X-Requested-With" \
  -X OPTIONS https://yourdomain.com/api/user/signin/
```

---

**Remember**: Security is an ongoing process, not a one-time setup. Regularly review and update your security measures!

---

**Last Updated**: January 2026  
**Review Frequency**: Quarterly
