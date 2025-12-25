# 📦 Push Your Code to GitHub

## Step 1: Set Git User (If Not Set)

Run these commands (replace with your info):

```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

## Step 2: Commit Your Code

```bash
cd C:\Users\alohp
git commit -m "Initial commit: Flashcard app with Groq AI integration"
```

## Step 3: Create GitHub Repository

1. Go to https://github.com/new
2. Repository name: `flashcard-app` (or your choice)
3. Description: "AI-powered flashcard generator using Groq"
4. Choose: **Public** or **Private**
5. **DO NOT** initialize with README, .gitignore, or license
6. Click **"Create repository"**

## Step 4: Push to GitHub

After creating the repo, GitHub will show you commands. Use these:

```bash
git remote add origin https://github.com/YOUR_USERNAME/flashcard-app.git
git branch -M main
git push -u origin main
```

**Replace `YOUR_USERNAME` with your GitHub username!**

## Step 5: Deploy!

Once pushed to GitHub:

1. **Railway**: Go to https://railway.app → "New Project" → "Deploy from GitHub repo"
2. **Render**: Go to https://render.com → "New +" → "Web Service" → Connect GitHub

**That's it!** Your code is now on GitHub and ready to deploy! 🚀


