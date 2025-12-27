# 🔧 Fix "No module named pip" Error

## Problem

Railway build failing with:
```
/root/.nix-profile/bin/python: No module named pip
```

## Root Cause

The Python installation from Nix doesn't include pip by default. We need to explicitly install pip as a package.

## Solution

I've updated `nixpacks.toml` to include pip:

**Before (WRONG):**
```toml
[phases.setup]
nixPkgs = ["python312"]  # ❌ pip not included
```

**After (CORRECT):**
```toml
[phases.setup]
nixPkgs = ["python312", "python312Packages.pip"]  # ✅ pip included
```

## Alternative Solutions

### Option 1: Use ensurepip (Built-in)

If the above doesn't work, we can use Python's built-in ensurepip:

```toml
[phases.install]
cmds = [
  "python -m ensurepip --upgrade",
  "python -m pip install --upgrade pip",
  "pip install -r requirements.txt",
  "python manage.py collectstatic --noinput",
  "python manage.py migrate --noinput"
]
```

### Option 2: Install pip via get-pip.py

```toml
[phases.install]
cmds = [
  "curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py",
  "python get-pip.py",
  "pip install -r requirements.txt",
  "python manage.py collectstatic --noinput",
  "python manage.py migrate --noinput"
]
```

### Option 3: Let Railway Auto-Detect

Remove `nixpacks.toml` and let Railway auto-detect:
- Railway will use its own Python setup which includes pip
- Set Release Command manually in dashboard: `python manage.py migrate --noinput`

## What I've Done

✅ Updated `nixpacks.toml` to include `python312Packages.pip`
✅ Changed commands to use `pip` directly (since it's now a package)

## After Fix

Railway should now:
1. Install Python 3.12
2. Install pip package
3. Upgrade pip
4. Install requirements
5. Run collectstatic
6. Run migrations
7. Start gunicorn

## If Still Failing

Try removing `nixpacks.toml` entirely and:
1. Let Railway auto-detect Python
2. Set commands manually in Railway dashboard:
   - **Release Command**: `python manage.py migrate --noinput`
   - **Start Command**: `gunicorn flashcard_app.wsgi --log-file -`

Railway's auto-detection usually handles pip correctly.

**The fix is pushed. Try redeploying!** 🚀


