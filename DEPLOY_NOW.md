# 🚀 Deploy Your Flashcard App - Step by Step

## Quick Deploy Options

### Option 1: Railway (Easiest - Recommended) ⭐

**Free tier includes**: 500 hours/month, $5 credit

#### Steps:

1. **Sign up**: Go to https://railway.app and sign up (free)

2. **Install Railway CLI**:
   ```bash
   npm install -g @railway/cli
   ```

3. **Login to Railway**:
   ```bash
   railway login
   ```

4. **Initialize and Deploy**:
   ```bash
   # Make sure you're in the project directory
   cd C:\Users\alohp
   
   # Initialize Railway project
   railway init
   
   # Deploy
   railway up
   ```

5. **Set Environment Variables** in Railway Dashboard:
   - Go to your project → Variables tab
   - Add these:
     ```
     SECRET_KEY=ZiIlPgETX2Jto6WSYq-C06_WEs-9C967apVK32qHBvLaETyO95mUahyhjYU1JF2rUEM
     DEBUG=False
     ALLOWED_HOSTS=your-app-name.railway.app
     LLM_PROVIDER=groq
     GROQ_API_KEY=your-groq-api-key-here
     USE_LLM=true
     ```

6. **Get your URL**: Railway will give you a URL like `your-app.railway.app`

**Done!** Your app is live! 🎉

---

### Option 2: Render (Free Tier) ⭐

**Free tier**: 750 hours/month

#### Steps:

1. **Sign up**: Go to https://render.com and sign up (free)

2. **Create New Web Service**:
   - Click "New +" → "Web Service"
   - Connect your Git repository (GitHub/GitLab/Bitbucket)
   - Or use the `render.yaml` file I created

3. **If using Git**:
   - **Build Command**: `pip install -r requirements.txt && python manage.py collectstatic --noinput`
   - **Start Command**: `gunicorn flashcard_app.wsgi`
   - **Environment**: Python 3

4. **Set Environment Variables**:
   ```
   SECRET_KEY=ZiIlPgETX2Jto6WSYq-C06_WEs-9C967apVK32qHBvLaETyO95mUahyhjYU1JF2rUEM
   DEBUG=False
   ALLOWED_HOSTS=your-app.onrender.com
   LLM_PROVIDER=none
   USE_LLM=false
   ```

5. **Deploy**: Click "Create Web Service"

**Done!** Your app is live! 🎉

---

### Option 3: PythonAnywhere (Free Tier)

1. **Sign up**: https://www.pythonanywhere.com
2. **Upload code** via Git or files
3. **Configure Web App**:
   - Source code: `/home/yourusername/flashcard_app`
   - WSGI file: Point to `flashcard_app/wsgi.py`
4. **Set environment variables** in Web tab

---

## Pre-Deployment Checklist

Before deploying, make sure:

- ✅ All files are committed to Git (if using Git deployment)
- ✅ `.env` file is NOT committed (it's in .gitignore)
- ✅ Secret key is generated (I've provided one above)
- ✅ `DEBUG=False` in production
- ✅ `ALLOWED_HOSTS` includes your domain

## Environment Variables Needed

```env
SECRET_KEY=ZiIlPgETX2Jto6WSYq-C06_WEs-9C967apVK32qHBvLaETyO95mUahyhjYU1JF2rUEM
DEBUG=False
ALLOWED_HOSTS=your-domain.com
LLM_PROVIDER=none
USE_LLM=false
```

**Note**: Groq works perfectly on cloud platforms! Get your free API key from https://console.groq.com/keys

## Quick Deploy Commands

### Railway:
```bash
railway login
railway init
railway up
```

### Render (via Git):
```bash
git add .
git commit -m "Ready for deployment"
git push origin main
# Then connect repo in Render dashboard
```

## After Deployment

1. **Visit your app URL**
2. **Test file upload**
3. **Check admin panel** (if you created superuser)
4. **Monitor logs** in your platform's dashboard

## Troubleshooting

### "Application Error"
- Check environment variables are set correctly
- Check logs in platform dashboard
- Verify `ALLOWED_HOSTS` includes your domain

### "Static files not loading"
- Make sure `collectstatic` ran during build
- Check WhiteNoise is in MIDDLEWARE

### "Database errors"
- Make sure migrations ran: `python manage.py migrate`
- Check database is accessible

## Need Help?

- Railway Docs: https://docs.railway.app
- Render Docs: https://render.com/docs
- Django Deployment: https://docs.djangoproject.com/en/4.2/howto/deployment/

**Your app is ready to deploy! Choose a platform above and follow the steps.** 🚀

