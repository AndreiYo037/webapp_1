# 📋 Railway Commands Explained

## Railway Command Types

### 1. **Release Command** / **Pre-deployment Command**
- **Same thing!** Railway uses both terms interchangeably
- **When it runs**: Before the service starts (during deployment)
- **Purpose**: Run setup tasks like database migrations
- **Example**: `python manage.py migrate --noinput`
- **Runs**: Once per deployment, before the service starts

### 2. **Build Command**
- **When it runs**: During the build phase (before deployment)
- **Purpose**: Install dependencies, compile assets, etc.
- **Example**: `pip install -r requirements.txt && python manage.py collectstatic --noinput`
- **Runs**: During build, creates the deployment image

### 3. **Start Command**
- **When it runs**: After deployment, to start the service
- **Purpose**: Start your application server
- **Example**: `gunicorn flashcard_app.wsgi --log-file -`
- **Runs**: Continuously (keeps your app running)

## For Your Django App

### Recommended Configuration:

**Build Command** (optional - Railway auto-detects):
```
python -m pip install --upgrade pip && pip install -r requirements.txt && python manage.py collectstatic --noinput
```

**Release Command** / **Pre-deployment Command**:
```
python manage.py migrate --noinput
```

**Start Command**:
```
gunicorn flashcard_app.wsgi --log-file -
```

## Where to Find in Railway

1. **Railway Dashboard** → Your Service → **Settings**
2. Scroll to **Build & Deploy** section
3. You'll see:
   - **Build Command** (optional)
   - **Release Command** or **Pre-deployment Command** (same thing!)
   - **Start Command**

## Execution Order

1. **Build Command** runs first (if set)
2. **Release/Pre-deployment Command** runs next
3. **Start Command** runs last (keeps running)

## Quick Answer

**Yes!** "Release Command" = "Pre-deployment Command" in Railway. Use either one - they're the same thing.

Set it to: `python manage.py migrate --noinput`


