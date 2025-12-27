# Push to Existing GitHub Repository

## Quick Command

Replace `YOUR_GITHUB_REPO_URL` with your actual repository URL:

```bash
cd C:\flashcard_app

# Add your existing repository as remote
git remote add origin YOUR_GITHUB_REPO_URL

# Push to your repository
git push -u origin main
```

## Repository URL Format

Your GitHub repository URL will look like one of these:

- HTTPS: `https://github.com/username/repository-name.git`
- SSH: `git@github.com:username/repository-name.git`

## If Repository Already Has Content

If your existing repository has commits, you may need to pull first:

```bash
git pull origin main --allow-unrelated-histories
```

Then push:
```bash
git push -u origin main
```

## Force Push (Only if needed)

⚠️ **Warning**: Only use if you want to overwrite existing content:

```bash
git push -u origin main --force
```

