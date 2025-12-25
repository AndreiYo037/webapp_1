# 🚨 URGENT: Fix Database Migrations Not Running

## Problem

You're still getting: `no such table: flashcards_flashcardset`

This means migrations are **NOT running** during deployment.

## Why This Happens

Even though `nixpacks.toml` includes migrations, Railway might:
1. Not be using the nixpacks.toml file
2. Need the Release Command set manually in the dashboard
3. Have migrations running but failing silently

## SOLUTION: Set Release Command in Railway Dashboard

**This is the MOST RELIABLE way to ensure migrations run:**

### Step-by-Step:

1. **Go to Railway Dashboard**
   - Open your project
   - Click on your service (the one that's failing)

2. **Open Settings**
   - Click the **Settings** tab

3. **Find "Deploy" Section**
   - Scroll down to **Deploy** or **Build & Deploy** section
   - Look for **"Release Command"** or **"Pre-deployment Command"**

4. **Add Release Command:**
   ```
   python manage.py migrate --noinput
   ```

5. **Verify Start Command:**
   Make sure **Start Command** is:
   ```
   gunicorn flashcard_app.wsgi --log-file -
   ```

6. **Save**
   - Click **Save** or the changes auto-save
   - Railway will automatically redeploy

7. **Wait for Deployment**
   - Check the deployment logs
   - Look for: `Applying flashcards.0001_initial... OK`

## Alternative: Check if Migrations Are in Build

If Release Command doesn't work, try adding migrations to Build Command:

**Build Command:**
```
python -m pip install --upgrade pip && python -m pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate --noinput
```

**Start Command:**
```
gunicorn flashcard_app.wsgi --log-file -
```

## Verify Migrations Ran

After deployment, check logs for:

```
Operations to perform:
  Apply all migrations: admin, auth, contenttypes, flashcards, sessions
Running migrations:
  Applying flashcards.0001_initial... OK
  Applying contenttypes.0001_initial... OK
  Applying auth.0001_initial... OK
  ...
```

## If Still Not Working

1. **Check Railway Logs:**
   - Go to your service → **Deployments**
   - Click on latest deployment → **View Logs**
   - Look for migration errors

2. **Manual Migration (Temporary Fix):**
   - Go to Railway → Your Service → **Shell** or **Console**
   - Run: `python manage.py migrate`
   - This will create tables immediately

3. **Check Database:**
   - Verify you're using the correct database
   - Railway might be using a different SQLite file

## Quick Checklist

- [ ] Release Command set to: `python manage.py migrate --noinput`
- [ ] Start Command set to: `gunicorn flashcard_app.wsgi --log-file -`
- [ ] Saved settings in Railway
- [ ] Redeployed (automatic or manual)
- [ ] Checked logs for migration output
- [ ] Verified tables exist (if you have database access)

## Most Important Step

**SET THE RELEASE COMMAND IN RAILWAY DASHBOARD!**

This is the most reliable way to ensure migrations run every deployment.

**The command to set:**
```
python manage.py migrate --noinput
```


