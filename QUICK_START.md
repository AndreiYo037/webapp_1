# 🚀 Quick Start - Host Your Flashcard App

## Your app is production-ready! Here's how to host it:

### Option 1: Local Production Server (Test First)

**Windows:**
```bash
start_production.bat
```

**Linux/Mac:**
```bash
chmod +x start_production.sh
./start_production.sh
```

**Manual:**
```bash
# 1. Create .env file
copy .env.example .env

# 2. Edit .env and set:
#    SECRET_KEY=<generate-new-key>
#    DEBUG=False
#    ALLOWED_HOSTS=localhost,127.0.0.1

# 3. Collect static files
python manage.py collectstatic --noinput

# 4. Run server
gunicorn flashcard_app.wsgi --bind 0.0.0.0:8000
```

### Option 2: Railway (Recommended - Free & Easy)

1. **Sign up**: https://railway.app (free tier available)
2. **Install CLI**: `npm install -g @railway/cli`
3. **Deploy**:
   ```bash
   railway login
   railway init
   railway up
   ```
4. **Set environment variables** in Railway dashboard:
   - `SECRET_KEY` (generate new)
   - `DEBUG=False`
   - `ALLOWED_HOSTS=your-app.railway.app`

### Option 3: Render (Free Tier)

1. **Sign up**: https://render.com
2. **Create Web Service** from Git
3. **Build Command**: `pip install -r requirements.txt && python manage.py collectstatic --noinput`
4. **Start Command**: `gunicorn flashcard_app.wsgi`
5. **Set environment variables**

### Option 4: PythonAnywhere (Free Tier)

1. **Sign up**: https://www.pythonanywhere.com
2. **Upload code** via Git
3. **Configure Web App**
4. **Set environment variables**

## Generate Secret Key

```bash
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

Copy the output to your `.env` file as `SECRET_KEY=...`

## Environment Variables Needed

```env
SECRET_KEY=your-generated-key-here
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
LLM_PROVIDER=ollama
OLLAMA_MODEL=mistral
USE_LLM=true
```

## Full Deployment Guide

See `DEPLOYMENT_GUIDE.md` for detailed instructions on all platforms.

## Current Status

✅ Production settings configured
✅ Security settings enabled
✅ Static files handled (WhiteNoise)
✅ Gunicorn configured
✅ Deployment files created
✅ Ready to deploy!

## Test Locally First

```bash
# Set up .env
copy .env.example .env
# Edit .env with production values

# Run production server
gunicorn flashcard_app.wsgi --bind 0.0.0.0:8000
```

Visit: http://localhost:8000

Your app is ready! 🎉


