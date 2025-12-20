# 🚀 Deployment Guide - Flashcard App

## Production-Ready Setup Complete! ✅

Your app is now configured for production deployment with:
- ✅ Security settings configured
- ✅ Static file handling (WhiteNoise)
- ✅ Production server (Gunicorn)
- ✅ Environment-based configuration

## Deployment Options

### Option 1: Local Production Server (Quick Start)

**Best for**: Testing production setup locally

```bash
# 1. Install production dependencies
pip install -r requirements.txt

# 2. Set environment variables
# Create .env file with:
SECRET_KEY=your-generated-secret-key
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1

# 3. Collect static files
python manage.py collectstatic --noinput

# 4. Run with Gunicorn
gunicorn flashcard_app.wsgi --bind 0.0.0.0:8000
```

### Option 2: Railway (Recommended - Easy & Free Tier)

**Best for**: Quick cloud deployment with free tier

1. **Sign up**: https://railway.app
2. **Install Railway CLI**:
   ```bash
   npm install -g @railway/cli
   railway login
   ```
3. **Deploy**:
   ```bash
   railway init
   railway up
   ```
4. **Set environment variables** in Railway dashboard:
   - `SECRET_KEY` (generate new one)
   - `DEBUG=False`
   - `ALLOWED_HOSTS=your-app.railway.app`
   - `LLM_PROVIDER=ollama`

**Free tier includes**: 500 hours/month, $5 credit

### Option 3: Render (Free Tier Available)

**Best for**: Simple deployment with PostgreSQL option

1. **Sign up**: https://render.com
2. **Create new Web Service**
3. **Connect your Git repository**
4. **Configure**:
   - Build Command: `pip install -r requirements.txt && python manage.py collectstatic --noinput`
   - Start Command: `gunicorn flashcard_app.wsgi`
5. **Set environment variables** in Render dashboard

**Free tier**: 750 hours/month

### Option 4: PythonAnywhere (Free Tier)

**Best for**: Python-focused hosting

1. **Sign up**: https://www.pythonanywhere.com
2. **Upload your code** via Git or files
3. **Configure Web App**:
   - Source code: `/home/yourusername/flashcard_app`
   - WSGI file: Point to `flashcard_app/wsgi.py`
4. **Set environment variables** in Web tab

**Free tier**: Limited but good for testing

### Option 5: Heroku (Paid, but reliable)

**Best for**: Production apps with budget

1. **Install Heroku CLI**
2. **Login**: `heroku login`
3. **Create app**: `heroku create your-app-name`
4. **Set config vars**:
   ```bash
   heroku config:set SECRET_KEY=your-key
   heroku config:set DEBUG=False
   heroku config:set ALLOWED_HOSTS=your-app.herokuapp.com
   ```
5. **Deploy**: `git push heroku main`

### Option 6: DigitalOcean App Platform

**Best for**: Scalable production apps

1. **Sign up**: https://www.digitalocean.com
2. **Create App** from GitHub
3. **Configure environment variables**
4. **Deploy**

## Pre-Deployment Checklist

### 1. Generate Secret Key
```bash
python -c "import secrets; print(secrets.token_urlsafe(50))"
```
Add to `.env` as `SECRET_KEY`

### 2. Update ALLOWED_HOSTS
In `.env`, set:
```
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
```

### 3. Set DEBUG=False
```
DEBUG=False
```

### 4. Collect Static Files
```bash
python manage.py collectstatic --noinput
```

### 5. Run Migrations
```bash
python manage.py migrate
```

### 6. Create Superuser (if needed)
```bash
python manage.py createsuperuser
```

## Environment Variables for Production

Create `.env` file with:

```env
# Django Settings
SECRET_KEY=your-generated-secret-key-here
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# LLM Configuration
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=mistral

USE_LLM=true
```

## Quick Local Production Test

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set up .env file
cp .env.example .env
# Edit .env with production values

# 3. Collect static files
python manage.py collectstatic --noinput

# 4. Run with Gunicorn
gunicorn flashcard_app.wsgi --bind 0.0.0.0:8000

# Or use the config file
gunicorn -c gunicorn_config.py flashcard_app.wsgi
```

## Database Considerations

**Current**: SQLite (good for small apps)
**For production**: Consider PostgreSQL
- Railway: Free PostgreSQL addon
- Render: Free PostgreSQL tier
- Heroku: Postgres addon

To migrate to PostgreSQL:
1. Add `psycopg2-binary` to requirements.txt
2. Update DATABASES in settings.py
3. Run migrations

## Static Files

WhiteNoise is configured to serve static files in production.
No need for separate static file hosting!

## Media Files

For production, consider:
- **AWS S3** for media storage
- **Cloudinary** for images
- **Railway/Render**: Use persistent volumes

## LLM in Production

### Option A: Ollama (Local)
- Only works if Ollama is on same server
- Best for: Self-hosted deployments

### Option B: Hugging Face Inference API (Free Tier)
- Works from cloud
- Free tier available
- Best for: Cloud deployments without local Ollama

### Option C: Hugging Face (Free Tier)
- Good free tier
- Works from cloud
- Best for: Cost-effective cloud deployment

## Monitoring & Logging

Add to your deployment:
- **Sentry** for error tracking
- **Logging** to files or services
- **Health checks** endpoint

## Security Checklist

✅ Secret key generated and secure
✅ DEBUG=False in production
✅ ALLOWED_HOSTS configured
✅ HTTPS enabled (if using SSL)
✅ CSRF and session cookies secure
✅ Static files served via WhiteNoise

## Need Help?

- Check Django deployment docs: https://docs.djangoproject.com/en/4.2/howto/deployment/
- Railway docs: https://docs.railway.app
- Render docs: https://render.com/docs

## Quick Deploy Commands

```bash
# Railway
railway up

# Render (via Git)
git push origin main  # Auto-deploys

# Heroku
git push heroku main

# Local production
gunicorn flashcard_app.wsgi --bind 0.0.0.0:8000
```

Your app is ready to deploy! 🎉

