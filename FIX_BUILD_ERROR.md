# 🔧 Fix Railway Build Error - "pip: command not found"

## Problem

Railway deployment is failing with:
```
/bin/bash: line 1: pip: command not found
"pip install -r requirements.txt" did not complete successfully: exit code: 127
```

## Solution

Railway uses Nixpacks which auto-detects Python, but sometimes needs explicit configuration.

### Option 1: Use Nixpacks Configuration (Recommended)

I've updated `nixpacks.toml` to explicitly include pip. Railway should auto-detect this file.

**If it still doesn't work, manually configure in Railway:**

1. Go to Railway Dashboard → Your Service → Settings
2. Scroll to **Build & Deploy**
3. **Build Command**: Leave empty (let Nixpacks handle it)
4. **Start Command**: `gunicorn flashcard_app.wsgi --log-file -`
5. **Release Command**: `python manage.py migrate --noinput`

### Option 2: Use Python Module Syntax

If pip still isn't found, Railway might need Python module syntax:

**In Railway Settings → Build Command:**
```
python -m pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate --noinput
```

### Option 3: Check Python Version

Make sure `runtime.txt` specifies Python version:
```
python-3.12.0
```

I've verified this is set correctly.

### Option 4: Manual Build Command

If auto-detection fails, set in Railway:

**Build Command:**
```
python -m pip install --upgrade pip && pip install -r requirements.txt && python manage.py collectstatic --noinput
```

**Release Command:**
```
python manage.py migrate --noinput
```

**Start Command:**
```
gunicorn flashcard_app.wsgi --log-file -
```

## What I've Fixed

✅ Updated `nixpacks.toml` to include pip explicitly
✅ Simplified `railway.json` (removed buildCommand - let Nixpacks handle it)
✅ Verified `runtime.txt` has correct Python version

## Steps to Fix

1. **Go to Railway Dashboard** → Your Service → Settings
2. **Build & Deploy** section:
   - **Build Command**: Leave empty OR use: `python -m pip install --upgrade pip && pip install -r requirements.txt && python manage.py collectstatic --noinput`
   - **Release Command**: `python manage.py migrate --noinput`
   - **Start Command**: `gunicorn flashcard_app.wsgi --log-file -`
3. **Save** and Railway will redeploy
4. **Check logs** to verify build succeeds

## Verify Build Success

After redeploy, check logs for:
```
✓ Installing dependencies
✓ Collecting static files
✓ Running migrations
✓ Starting gunicorn
```

## Alternative: Use Dockerfile

If Nixpacks continues to have issues, we can create a Dockerfile. Let me know if you need this!

## Still Having Issues?

1. Check Railway logs for specific error
2. Verify Python version in `runtime.txt` matches Railway's Python
3. Try the manual build command above
4. Consider using Railway's "Deploy from GitHub" with auto-detection

**The configuration files are updated. Try redeploying!** 🚀


