# 🚀 Push Your Code to GitHub - Quick Guide

## ✅ Your Code is Committed!

Your code has been committed locally. Now push it to GitHub:

## Step 1: Create GitHub Repository

1. **Go to**: https://github.com/new
2. **Repository name**: `flashcard-app` (or any name you like)
3. **Description**: "AI-powered flashcard generator using Groq"
4. **Visibility**: Choose **Public** (for free hosting) or **Private**
5. **Important**: 
   - ❌ **DO NOT** check "Add a README file"
   - ❌ **DO NOT** check "Add .gitignore"
   - ❌ **DO NOT** check "Choose a license"
6. **Click**: "Create repository"

## Step 2: Connect and Push

After creating the repo, GitHub will show you commands. Run these in your terminal:

```bash
cd C:\Users\alohp

# Add GitHub as remote (replace YOUR_USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/flashcard-app.git

# Rename branch to main (if needed)
git branch -M main

# Push your code
git push -u origin main
```

**Example** (if your username is `johnsmith`):
```bash
git remote add origin https://github.com/johnsmith/flashcard-app.git
git branch -M main
git push -u origin main
```

## Step 3: Deploy!

Once your code is on GitHub:

### Railway (Easiest):
1. Go to https://railway.app
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose your `flashcard-app` repository
5. Set environment variables (see below)
6. Deploy!

### Render:
1. Go to https://render.com
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Set environment variables
5. Deploy!

## Environment Variables to Set

In Railway or Render dashboard, add these:

```
SECRET_KEY=FPIE5v8gRW-2vb8L4VytlVr49za77vwhtCfDodiqr_DvDaY1mtEagdvxNUdpYWW00hY
DEBUG=False
ALLOWED_HOSTS=*.railway.app
LLM_PROVIDER=groq
GROQ_API_KEY=your-groq-api-key-here
GROQ_MODEL=llama-3.3-70b-versatile
USE_LLM=true
```

## Need Help?

- **GitHub**: https://docs.github.com/en/get-started
- **Railway**: https://docs.railway.app
- **Render**: https://render.com/docs

**Your code is ready to push!** 🎉

