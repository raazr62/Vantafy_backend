# Cross-Origin Development Setup Guide

## Quick Start

### For Same-Origin Development (Both on localhost)

**Backend `.env`:**

```bash
DEBUG=True
CROSS_ORIGIN_DEVELOPMENT=False
```

**Frontend `.env`:**

```bash
VITE_BASE_URL=http://localhost:8000/api
```

✅ **Use this when**: Both developers running locally on their own machines

---

### For Cross-Origin Development (Distributed Team)

**Backend `.env`:**

```bash
DEBUG=True
CROSS_ORIGIN_DEVELOPMENT=True
```

**Frontend `.env`:**

```bash
VITE_BASE_URL=https://your-ngrok-url.ngrok-free.app/api
```

✅ **Use this when**:

- Backend developer in Dhaka using ngrok
- Frontend developer in another location
- Backend is HTTPS (ngrok), frontend is localhost

---

### For Production

**Backend `.env`:**

```bash
DEBUG=False
CROSS_ORIGIN_DEVELOPMENT=False
```

**Frontend `.env`:**

```bash
VITE_BASE_URL=https://api.yourdomain.com
```

✅ **Use this when**: Deploying to production servers

---

## What Happens Automatically

### When `CROSS_ORIGIN_DEVELOPMENT=True`

```
🌐 Cross-origin development mode: Cookies will work across different domains (ngrok + localhost)

Cookie Settings:
- SameSite: None (allows cross-origin cookies)
- Secure: True (requires HTTPS - ngrok provides this)
- HttpOnly: True (XSS protection)
```

### When `CROSS_ORIGIN_DEVELOPMENT=False` and `DEBUG=True`

```
🏠 Same-origin development mode: Cookies will work on localhost only

Cookie Settings:
- SameSite: Lax (same-origin only)
- Secure: False (HTTP is fine for localhost)
- HttpOnly: True (XSS protection)
```

### When `DEBUG=False` (Production)

```
🔒 Production mode: Secure cookies enabled

Cookie Settings:
- SameSite: Lax (recommended for production)
- Secure: True (HTTPS required)
- HttpOnly: True (XSS protection)
```

---

## Example Scenarios

### Scenario 1: Solo Developer (Local Development)

You're developing both frontend and backend on your laptop.

**Backend `.env`:**

```bash
DEBUG=True
CROSS_ORIGIN_DEVELOPMENT=False
```

**Frontend `.env`:**

```bash
VITE_BASE_URL=http://localhost:8000/api
```

**Result**: ✅ Cookies work perfectly on localhost

---

### Scenario 2: Distributed Team Development

- Backend developer in Dhaka runs backend on ngrok: `https://abc123.ngrok-free.app`
- Frontend developer anywhere runs frontend on: `http://localhost:5173`

**Backend `.env`:**

```bash
DEBUG=True
CROSS_ORIGIN_DEVELOPMENT=True
```

**Frontend `.env`:**

```bash
VITE_BASE_URL=https://abc123.ngrok-free.app/api
```

**Result**: ✅ Cookies work across different domains

---

### Scenario 3: Production Deployment

Both frontend and backend deployed to production servers.

**Backend `.env`:**

```bash
DEBUG=False
CROSS_ORIGIN_DEVELOPMENT=False
```

**Frontend `.env`:**

```bash
VITE_BASE_URL=https://api.yourdomain.com
```

**Result**: ✅ Secure production cookies

---

## Troubleshooting

### ❌ Cookies not working in cross-origin development?

**Check:**

1. Is `CROSS_ORIGIN_DEVELOPMENT=True` in backend `.env`?
2. Is backend using HTTPS (ngrok provides this)?
3. Is `withCredentials: true` in frontend axios config? ✅ (already configured)
4. Is `X-Client-Type: web` header being sent? ✅ (already configured)

### ❌ Cookies not working in same-origin development?

**Check:**

1. Is `CROSS_ORIGIN_DEVELOPMENT=False` in backend `.env`?
2. Are both frontend and backend using `localhost` (not mixing with `127.0.0.1`)?
3. Frontend URL: `http://localhost:5173` ✅
4. Backend URL: `http://localhost:8000` ✅

---

## Important Notes

⚠️ **Never use `CROSS_ORIGIN_DEVELOPMENT=True` in production!**

⚠️ **Backend must be HTTPS when `CROSS_ORIGIN_DEVELOPMENT=True`** (ngrok provides this automatically)

✅ **Frontend can be HTTP (localhost) even in cross-origin mode**

✅ **The system automatically configures everything based on this one variable**

---

## Current Configuration

Your current setup is configured for **same-origin development** (both on localhost).

To switch to cross-origin development:

1. Backend developer: Add `CROSS_ORIGIN_DEVELOPMENT=True` to `.env`
2. Backend developer: Share ngrok URL with frontend developer
3. Frontend developer: Update `VITE_BASE_URL` to ngrok URL
4. Restart both servers

That's it! 🎉
