# 🔧 Fix Nixpacks Error - "undefined variable 'pip'"

## Problem

Railway build failing with:
```
error: undefined variable 'pip'
at /app/.nixpacks/nixpkgs-bc8f8d1be58e8c8383e683a06e1e1e57893fff87.nix:19:9
```

## Root Cause

In Nix/Nixpacks, `pip` is not a separate package - it comes bundled with Python. You cannot list `pip` in the `nixPkgs` array.

## Solution

I've fixed `nixpacks.toml`:

**Before (WRONG):**
```toml
[phases.setup]
nixPkgs = ["python312", "pip"]  # ❌ pip is not a valid Nix package
```

**After (CORRECT):**
```toml
[phases.setup]
nixPkgs = ["python312"]  # ✅ pip comes with Python

[phases.install]
cmds = [
  "python -m pip install --upgrade pip",  # ✅ Use python -m pip
  "python -m pip install -r requirements.txt",
  "python manage.py collectstatic --noinput",
  "python manage.py migrate --noinput"
]
```

## Key Changes

1. ✅ Removed `pip` from `nixPkgs` array
2. ✅ Changed `pip install` to `python -m pip install` (more reliable)
3. ✅ Pip is automatically available with Python

## What Happens Now

Railway will:
1. Install Python 3.12 (which includes pip)
2. Use `python -m pip` to install packages
3. Run collectstatic
4. Run migrations
5. Start gunicorn

## After Fix

The build should now succeed! Railway will automatically redeploy when it detects the change.

## Alternative: Use Railway's Auto-Detection

If you prefer, you can also:
1. Delete or rename `nixpacks.toml`
2. Let Railway auto-detect Python
3. Set commands manually in Railway dashboard:
   - **Release Command**: `python manage.py migrate --noinput`
   - **Start Command**: `gunicorn flashcard_app.wsgi --log-file -`

## Verification

After redeploy, check logs for:
```
✓ Installing Python 3.12
✓ Installing dependencies
✓ Collecting static files
✓ Running migrations
✓ Starting gunicorn
```

**The fix is pushed to GitHub. Railway should auto-redeploy!** 🚀


