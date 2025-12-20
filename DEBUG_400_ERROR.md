# 🔍 Debug 400 Bad Request Error

## Still Getting 400 Error?

Let's diagnose and fix this step by step.

## Step 1: Check What Error You're Getting

The 400 error could be from:
1. **ALLOWED_HOSTS** - Most common
2. **CSRF Token** - Common with forms
3. **Missing SECRET_KEY**
4. **Cookie security settings**

## Step 2: Enable DEBUG Temporarily

To see the actual error message:

**In Railway/Render Environment Variables:**
```
DEBUG=True
```

**Then redeploy and check:**
- You'll see the actual error message
- Look for "DisallowedHost" or "CSRF" errors

**⚠️ Remember to set DEBUG=False after debugging!**

## Step 3: Set ALLOWED_HOSTS Correctly

### For Railway:

**Option 1: Allow All Hosts** (Quick Fix)
```
ALLOW_ALL_HOSTS=true
```

**Option 2: Specific Domain**
```
ALLOWED_HOSTS=your-app-name.railway.app
```

**Option 3: All Railway Domains**
```
ALLOWED_HOSTS=*.railway.app
```

### For Render:

```
ALLOWED_HOSTS=*.onrender.com
```

## Step 4: Fix CSRF Issues

If you see CSRF errors, add:

**Railway:**
```
CSRF_TRUSTED_ORIGINS=https://your-app-name.railway.app
```

**Render:**
```
CSRF_TRUSTED_ORIGINS=https://your-app.onrender.com
```

## Step 5: Disable Cookie Security (If Still Failing)

Some platforms need these disabled:

```
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False
```

## Complete Environment Variables for Testing

Try these settings to get it working:

```
DEBUG=True
ALLOW_ALL_HOSTS=true
SECRET_KEY=FPIE5v8gRW-2vb8L4VytlVr49za77vwhtCfDodiqr_DvDaY1mtEagdvxNUdpYWW00hY
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False
SECURE_SSL_REDIRECT=False
LLM_PROVIDER=groq
GROQ_API_KEY=your-groq-api-key-here
GROQ_MODEL=llama-3.3-70b-versatile
USE_LLM=true
```

**After it works, set DEBUG=False and enable security settings.**

## Step 6: Check Logs

**Railway:**
- Service → Deployments → Latest → View Logs
- Look for "DisallowedHost" or error messages

**Render:**
- Service → Logs tab
- Check for error messages

## Common Error Messages

### "DisallowedHost"
→ Set `ALLOW_ALL_HOSTS=true` or `ALLOWED_HOSTS=your-domain`

### "CSRF verification failed"
→ Add `CSRF_TRUSTED_ORIGINS=https://your-domain`

### "Invalid HTTP_HOST header"
→ Set `ALLOWED_HOSTS` correctly

## Quick Test Configuration

Use this minimal config to test:

```
DEBUG=True
ALLOW_ALL_HOSTS=true
SECRET_KEY=FPIE5v8gRW-2vb8L4VytlVr49za77vwhtCfDodiqr_DvDaY1mtEagdvxNUdpYWW00hY
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False
```

If this works, then gradually enable security settings.

## Still Not Working?

1. **Check the exact URL** you're accessing
2. **Check logs** for specific error messages
3. **Try accessing via different browser/incognito**
4. **Verify environment variables are saved** (some platforms need manual redeploy)

## What I Fixed

✅ Better ALLOWED_HOSTS handling
✅ Auto-allow all hosts in production if not set (prevents 400 errors)
✅ CSRF_TRUSTED_ORIGINS auto-configuration
✅ Cookie security settings made optional
✅ Better error handling

**Push the latest changes and update your environment variables!**

