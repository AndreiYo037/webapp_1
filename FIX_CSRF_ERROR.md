# 🔧 Fix CSRF Verification Failed (403 Error)

## Problem

Getting: `CSRF verification failed. Request aborted.`
```
Origin checking failed - https://web-production-db558.up.railway.app does not match any trusted origins.
```

## Root Cause

Django's CSRF protection requires the domain to be in `CSRF_TRUSTED_ORIGINS`. Your Railway domain isn't in the list.

## Solution

### Option 1: Set Environment Variable (Recommended)

**In Railway Dashboard → Your Service → Variables:**

Add:
```
CSRF_TRUSTED_ORIGINS=https://web-production-db558.up.railway.app
```

Or for all Railway domains:
```
CSRF_TRUSTED_ORIGINS=https://*.railway.app
```

### Option 2: Auto-Detection (Already Implemented)

I've updated `settings.py` to automatically build `CSRF_TRUSTED_ORIGINS` from `ALLOWED_HOSTS`. 

**Make sure `ALLOWED_HOSTS` includes your domain:**

In Railway Variables:
```
ALLOWED_HOSTS=web-production-db558.up.railway.app
```

Or allow all Railway domains:
```
ALLOWED_HOSTS=*.railway.app
```

The CSRF trusted origins will be auto-generated from this.

## Quick Fix

**Set these environment variables in Railway:**

```
ALLOWED_HOSTS=*.railway.app
CSRF_TRUSTED_ORIGINS=https://*.railway.app
```

Or for your specific domain:
```
ALLOWED_HOSTS=web-production-db558.up.railway.app
CSRF_TRUSTED_ORIGINS=https://web-production-db558.up.railway.app
```

## What I've Fixed

✅ Updated `settings.py` to auto-generate `CSRF_TRUSTED_ORIGINS` from `ALLOWED_HOSTS`
✅ Added support for wildcard domains
✅ Made it work in both DEBUG and production modes

## After Setting Variables

1. **Save** the environment variables in Railway
2. **Wait** for auto-redeploy (or manually redeploy)
3. **Try accessing** your app again
4. **CSRF errors should be gone!**

## Verify It's Working

After setting the variables, you should be able to:
- ✅ Access the homepage
- ✅ Upload files
- ✅ Submit forms
- ✅ No more 403 CSRF errors

## Complete Environment Variables Checklist

Make sure you have all these set in Railway:

```
SECRET_KEY=FPIE5v8gRW-2vb8L4VytlVr49za77vwhtCfDodiqr_DvDaY1mtEagdvxNUdpYWW00hY
DEBUG=False
ALLOWED_HOSTS=*.railway.app
CSRF_TRUSTED_ORIGINS=https://*.railway.app
LLM_PROVIDER=groq
GROQ_API_KEY=your-groq-api-key-here
GROQ_MODEL=llama-3.3-70b-versatile
USE_LLM=true
```

**The fix is pushed to GitHub. Set the environment variables and redeploy!** 🚀


