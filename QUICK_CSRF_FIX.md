# Quick CSRF Fix for Railway

## Immediate Fix - Set Environment Variable

The fastest way to fix the CSRF error is to set the environment variable in Railway:

1. Go to Railway Dashboard → Your Service → Variables
2. Add:
   ```
   CSRF_TRUSTED_ORIGINS=https://web-production-db558.up.railway.app
   ```
3. Save - Railway will redeploy automatically

## What Was Done

1. ✅ Added `CSRF_TRUSTED_ORIGINS` configuration
2. ✅ Created middleware to dynamically add Railway domains
3. ✅ Pushed fixes to GitHub

## How It Works

- **Option 1 (Recommended)**: Set `CSRF_TRUSTED_ORIGINS` environment variable with your exact Railway domain
- **Option 2**: The middleware will automatically add the request origin if it matches `ALLOWED_HOSTS`

## After Setting Environment Variable

Railway will redeploy and the registration form (and all other forms) will work without CSRF errors.

## Test

After redeploy, try registering again. The CSRF error should be gone!


