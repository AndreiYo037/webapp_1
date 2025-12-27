# CSRF Error Fix

## Issue Fixed

The CSRF (Cross-Site Request Forgery) error when registering has been fixed by adding `CSRF_TRUSTED_ORIGINS` to settings.

## What Was Changed

Added `CSRF_TRUSTED_ORIGINS` configuration to allow Railway domains:
- `https://*.up.railway.app`
- `https://*.railway.app`

## Railway Environment Variable (Optional)

You can also set this explicitly in Railway Dashboard → Variables:

```
CSRF_TRUSTED_ORIGINS=https://web-production-db558.up.railway.app
```

Or for multiple domains:
```
CSRF_TRUSTED_ORIGINS=https://web-production-db558.up.railway.app,https://yourdomain.com
```

## After Push

Railway will automatically redeploy. The registration form should now work without CSRF errors.

## What This Fixes

- ✅ Registration form submission
- ✅ Login form submission  
- ✅ All POST requests from Railway domain
- ✅ Stripe Checkout redirects

The fix has been pushed to GitHub and Railway will redeploy automatically.


