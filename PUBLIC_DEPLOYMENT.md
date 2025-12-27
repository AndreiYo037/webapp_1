# 🌐 Deploy Your Flashcard App for Public Access

## Quick Deploy - Make Your App Public!

### Option 1: Railway (Recommended - Easiest) ⭐

**Free tier**: 500 hours/month, $5 credit

#### Step-by-Step:

1. **Sign up at Railway**:
   - Go to https://railway.app
   - Click "Start a New Project"
   - Sign up with GitHub/Google (free)

2. **Deploy via GitHub (Easiest)**:
   
   a. **Push your code to GitHub** (if not already):
   ```bash
   git init
   git add .
   git commit -m "Initial commit - Flashcard app"
   # Create a new repo on GitHub, then:
   git remote add origin https://github.com/yourusername/flashcard-app.git
   git push -u origin main
   ```
   
   b. **In Railway Dashboard**:
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your repository
   - Railway will auto-detect Django

3. **Set Environment Variables** in Railway:
   
   Go to your project → Variables tab → Add:
   ```
   SECRET_KEY=FPIE5v8gRW-2vb8L4VytlVr49za77vwhtCfDodiqr_DvDaY1mtEagdvxNUdpYWW00hY
   DEBUG=False
   ALLOWED_HOSTS=*.railway.app
   LLM_PROVIDER=groq
   GROQ_API_KEY=your-groq-api-key-here
   GROQ_MODEL=llama-3.3-70b-versatile
   USE_LLM=true
   ```

4. **Deploy Settings**:
   - Build Command: `pip install -r requirements.txt && python manage.py collectstatic --noinput`
   - Start Command: `gunicorn flashcard_app.wsgi`
   - Python Version: 3.12

5. **Get Your Public URL**:
   - Railway will give you: `your-app-name.railway.app`
   - Share this URL with anyone!

**Done! Your app is now public!** 🎉

---

### Option 2: Render (Free Tier) ⭐

**Free tier**: 750 hours/month

#### Steps:

1. **Sign up**: https://render.com (free)

2. **Create Web Service**:
   - Click "New +" → "Web Service"
   - Connect GitHub repository
   - Or use "Public Git repository" URL

3. **Configure**:
   - **Name**: `flashcard-app` (or your choice)
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt && python manage.py collectstatic --noinput`
   - **Start Command**: `gunicorn flashcard_app.wsgi`

4. **Set Environment Variables**:
   ```
   SECRET_KEY=FPIE5v8gRW-2vb8L4VytlVr49za77vwhtCfDodiqr_DvDaY1mtEagdvxNUdpYWW00hY
   DEBUG=False
   ALLOWED_HOSTS=your-app.onrender.com
   LLM_PROVIDER=groq
   GROQ_API_KEY=your-groq-api-key-here
   GROQ_MODEL=llama-3.3-70b-versatile
   USE_LLM=true
   ```

5. **Deploy**: Click "Create Web Service"

6. **Get URL**: `your-app.onrender.com`

**Done!** 🎉

---

## Quick Deploy Commands

### Railway (CLI Method):

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Deploy
cd C:\Users\alohp
railway init
railway up
```

Then set environment variables in Railway dashboard.

### Render (Git Method):

```bash
# Push to GitHub first
git add .
git commit -m "Ready for public deployment"
git push origin main

# Then connect repo in Render dashboard
```

---

## Environment Variables for Public Deployment

**Copy these to your platform's environment variables:**

```env
SECRET_KEY=FPIE5v8gRW-2vb8L4VytlVr49za77vwhtCfDodiqr_DvDaY1mtEagdvxNUdpYWW00hY
DEBUG=False
ALLOWED_HOSTS=*.railway.app
# OR for Render: ALLOWED_HOSTS=your-app.onrender.com
LLM_PROVIDER=groq
GROQ_API_KEY=your-groq-api-key-here
GROQ_MODEL=llama-3.3-70b-versatile
USE_LLM=true
```

**Important**: 
- Replace `*.railway.app` with your actual domain after deployment
- Or use `*` to allow all domains (less secure but easier)

---

## After Deployment

1. **Visit your public URL** (e.g., `your-app.railway.app`)
2. **Test file upload** - Make sure Groq is working
3. **Share the URL** - Anyone can now access your app!
4. **Monitor usage** - Check platform dashboard for stats

---

## What Users Can Do

Once deployed, anyone can:
- ✅ Upload files (PDF, DOC, XLS, TXT)
- ✅ Generate AI-powered flashcards (using Groq)
- ✅ View and study flashcards
- ✅ Access from anywhere in the world!

---

## Security Notes

✅ **Secret Key**: Already generated and secure
✅ **DEBUG**: Set to False for production
✅ **ALLOWED_HOSTS**: Configured for your domain
✅ **Groq API Key**: Keep it secret (in environment variables)

---

## Troubleshooting

### "Application Error"
- Check environment variables are set
- Verify `ALLOWED_HOSTS` includes your domain
- Check logs in platform dashboard

### "Static files not loading"
- Build command should include `collectstatic`
- WhiteNoise is configured for static files

### "Groq not working"
- Verify `GROQ_API_KEY` is set correctly
- Check Groq API key is valid
- App will fall back to rule-based if Groq fails

---

## Recommended: Railway

**Why Railway?**
- ✅ Easiest deployment
- ✅ Free tier available
- ✅ Auto-detects Django
- ✅ Simple environment variables
- ✅ Great documentation

**Get started**: https://railway.app

---

## Your App Will Be Public At:

After deployment, your app will be accessible at:
- **Railway**: `https://your-app-name.railway.app`
- **Render**: `https://your-app.onrender.com`

**Share this URL with anyone!** 🌍

---

Ready to deploy? Choose Railway or Render and follow the steps above! 🚀

