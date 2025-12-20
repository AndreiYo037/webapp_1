# 🔧 Fix "Bad Request" Error - Public Networking

## Problem

You're getting a "Bad Request (400)" error when accessing your deployed app via public URL.

## Common Causes

1. **ALLOWED_HOSTS not configured** - Your domain isn't in the allowed hosts list
2. **Environment variable not set** - ALLOWED_HOSTS environment variable missing
3. **Domain mismatch** - The domain you're accessing doesn't match what's configured

## Solution

### For Railway Deployment:

1. **Go to Railway Dashboard**:
   - Open your project
   - Click on your service
   - Go to **Variables** tab

2. **Update ALLOWED_HOSTS**:
   
   **Option A: Specific Domain** (Recommended)
   ```
   ALLOWED_HOSTS=your-app-name.railway.app
   ```
   Replace `your-app-name` with your actual Railway app name.

   **Option B: Allow All Railway Domains**
   ```
   ALLOWED_HOSTS=*.railway.app
   ```

   **Option C: Allow All Hosts** (Less secure, but works for testing)
   ```
   ALLOWED_HOSTS=*
   ```
   OR set:
   ```
   ALLOW_ALL_HOSTS=true
   ```

3. **Redeploy**:
   - Railway will automatically redeploy when you change environment variables
   - Or click "Redeploy" button

### For Render Deployment:

1. **Go to Render Dashboard**:
   - Open your service
   - Go to **Environment** tab

2. **Update ALLOWED_HOSTS**:
   ```
   ALLOWED_HOSTS=your-app.onrender.com
   ```
   Or for all Render domains:
   ```
   ALLOWED_HOSTS=*.onrender.com
   ```

3. **Save and Redeploy**

### Quick Fix (Allow All Hosts):

If you want a quick fix for testing, set:

**Railway:**
```
ALLOW_ALL_HOSTS=true
```

**Render:**
```
ALLOWED_HOSTS=*
```

⚠️ **Note**: Allowing all hosts is less secure. Use specific domains in production.

## Verify Your Domain

To find your exact domain:

**Railway:**
- Go to your service → Settings → Domains
- Copy the exact domain (e.g., `flashcard-app-production.up.railway.app`)

**Render:**
- Go to your service → Settings
- Your domain is shown at the top (e.g., `flashcard-app.onrender.com`)

## Complete Environment Variables Checklist

Make sure you have ALL these set:

```
SECRET_KEY=FPIE5v8gRW-2vb8L4VytlVr49za77vwhtCfDodiqr_DvDaY1mtEagdvxNUdpYWW00hY
DEBUG=False
ALLOWED_HOSTS=your-exact-domain.railway.app
# OR for testing: ALLOWED_HOSTS=*
LLM_PROVIDER=groq
GROQ_API_KEY=your-groq-api-key-here
GROQ_MODEL=llama-3.3-70b-versatile
USE_LLM=true
```

## After Fixing

1. **Wait for redeploy** (usually 1-2 minutes)
2. **Clear browser cache** (Ctrl+Shift+Delete)
3. **Try accessing your app again**
4. **Check logs** in Railway/Render dashboard if still having issues

## Still Not Working?

Check the logs in your deployment platform:
- **Railway**: Service → Deployments → Click latest deployment → View logs
- **Render**: Service → Logs tab

Look for errors related to:
- `DisallowedHost` 
- `Invalid HTTP_HOST header`
- `ALLOWED_HOSTS`

## Settings Updated

I've updated your `settings.py` to better handle ALLOWED_HOSTS:
- ✅ Handles empty strings properly
- ✅ Supports wildcard `*` for all hosts
- ✅ Supports `ALLOW_ALL_HOSTS=true` for quick testing
- ✅ Strips whitespace from host names

**Update your environment variables and redeploy!** 🚀

