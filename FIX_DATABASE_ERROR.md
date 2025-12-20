# 🔧 Fix "no such table" Database Error

## Problem

You're getting: `OperationalError: no such table: flashcards_flashcardset`

This means the database migrations haven't been run on your deployment.

## Solution

### For Railway:

**Option 1: Add Release Command** (Recommended)

1. Go to Railway Dashboard → Your Service
2. Click on **Settings**
3. Scroll to **Deploy**
4. Add **Release Command**:
   ```
   python manage.py migrate --noinput
   ```
5. Save and redeploy

**Option 2: Update Build Command**

1. Go to Railway Dashboard → Your Service
2. Click on **Settings**
3. Scroll to **Build & Deploy**
4. Update **Build Command** to:
   ```
   pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate --noinput
   ```
5. Save and redeploy

**Option 3: Use railway.json** (Already created)

I've created `railway.json` which includes migrations in the build command. Railway should auto-detect it.

### For Render:

The `render.yaml` has been updated to include migrations. If you're using Render:

1. The build command now includes: `python manage.py migrate --noinput`
2. Redeploy your service
3. Migrations will run automatically

## Manual Fix (If Needed)

If the above doesn't work, you can run migrations manually:

**Railway:**
1. Go to your service → **Deployments**
2. Click on the latest deployment
3. Open **Shell** or **Logs**
4. Run: `python manage.py migrate`

**Render:**
1. Go to your service → **Shell**
2. Run: `python manage.py migrate`

## Verify Migrations

After migrations run, you should see:
```
Operations to perform:
  Apply all migrations: admin, auth, contenttypes, flashcards, sessions
Running migrations:
  Applying flashcards.0001_initial... OK
  ...
```

## What I've Done

✅ Updated `render.yaml` to include migrations
✅ Created `railway.json` with migration command
✅ Created `nixpacks.toml` as alternative for Railway
✅ Updated `build.sh` (already had migrations)

## After Fixing

1. **Redeploy** your app
2. **Wait** for deployment to complete
3. **Check logs** to verify migrations ran
4. **Try accessing** your app again

The database tables should now be created! 🎉

## Still Having Issues?

If migrations still don't run:

1. **Check Railway/Render logs** for errors
2. **Verify migrations exist** in `flashcards/migrations/`
3. **Try manual migration** via shell/console
4. **Check database connection** (if using external DB)

