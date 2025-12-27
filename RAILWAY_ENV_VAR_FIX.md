# Railway ALLOWED_HOSTS Fix

## Quick Fix via Railway Dashboard

If the code fix doesn't work immediately, you can set the environment variable directly in Railway:

1. Go to Railway Dashboard → Your Service → Variables
2. Add/Update:
   ```
   ALLOWED_HOSTS=web-production-db558.up.railway.app,*
   ```
   Or simply:
   ```
   ALLOWED_HOSTS=*
   ```

3. Railway will automatically redeploy

## Why This Works

Setting `ALLOWED_HOSTS=*` in the environment variable will explicitly allow all hosts, bypassing any code issues.

## Alternative: Set Specific Domain

If you prefer to be more specific:
```
ALLOWED_HOSTS=web-production-db558.up.railway.app
```

But using `*` is simpler and works for all Railway domains.


