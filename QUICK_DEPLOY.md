# 🚀 Quick Deploy - Make Your App Public (5 Minutes)

## Fastest Way: Railway (No Git Needed!)

### Step 1: Sign Up (1 minute)
1. Go to https://railway.app
2. Click "Start a New Project"
3. Sign up with GitHub/Google (free)

### Step 2: Deploy (2 minutes)

**Option A: Deploy from GitHub** (Recommended)
1. Push your code to GitHub:
   ```bash
   git init
   git add .
   git commit -m "Flashcard app"
   # Create repo on GitHub, then:
   git remote add origin YOUR_GITHUB_REPO_URL
   git push -u origin main
   ```
2. In Railway: "New Project" → "Deploy from GitHub repo"
3. Select your repo

**Option B: Deploy via CLI** (No Git needed)
```bash
npm install -g @railway/cli
railway login
cd C:\Users\alohp
railway init
railway up
```

### Step 3: Set Environment Variables (1 minute)

In Railway Dashboard → Your Project → Variables:

```
SECRET_KEY=FPIE5v8gRW-2vb8L4VytlVr49za77vwhtCfDodiqr_DvDaY1mtEagdvxNUdpYWW00hY
DEBUG=False
ALLOWED_HOSTS=*.railway.app
LLM_PROVIDER=groq
GROQ_API_KEY=your-groq-api-key-here
GROQ_MODEL=llama-3.3-70b-versatile
USE_LLM=true
```

### Step 4: Get Your URL (1 minute)

Railway will give you: `your-app-name.railway.app`

**That's it! Your app is now public!** 🎉

---

## Alternative: Render (Also Free)

1. Sign up: https://render.com
2. "New +" → "Web Service"
3. Connect GitHub repo
4. Set environment variables (same as above)
5. Deploy!

---

## Your Public URL

After deployment, share this URL:
- **Railway**: `https://your-app-name.railway.app`
- **Render**: `https://your-app.onrender.com`

**Anyone can now access your flashcard app!** 🌍

See `PUBLIC_DEPLOYMENT.md` for detailed instructions.

