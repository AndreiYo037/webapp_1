# Railway Deployment Guide

## Quick Setup

### 1. Push to GitHub

```bash
cd C:\flashcard_app

# If you haven't created a GitHub repo yet:
# 1. Go to GitHub and create a new repository
# 2. Then run:

git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
git branch -M main
git push -u origin main
```

### 2. Deploy on Railway

1. **Go to Railway**: https://railway.app
2. **Sign up/Login** with GitHub
3. **New Project** → **Deploy from GitHub repo**
4. **Select your repository**
5. **Add PostgreSQL**:
   - Click "+ New" → "Database" → "Add PostgreSQL"
   - Railway will automatically set `DATABASE_URL`

6. **Set Environment Variables**:
   Click on your service → Variables tab → Add:

   ```
   SECRET_KEY=your-secret-key-here
   DEBUG=False
   ALLOWED_HOSTS=your-app.railway.app
   USE_LLM=true
   LLM_PROVIDER=groq
   GROQ_API_KEY=your-groq-api-key-here
   ```

   Generate SECRET_KEY:
   ```bash
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```

   **Get Groq API Key (FREE)**:
   1. Go to https://console.groq.com/
   2. Sign up/Login (free account)
   3. Go to API Keys section
   4. Create a new API key
   5. Copy the key (starts with `gsk_`)
   6. Add it as `GROQ_API_KEY` in Railway variables

7. **Optional - Email Configuration**:
   ```
   EMAIL_HOST=smtp.sendgrid.net
   EMAIL_PORT=587
   EMAIL_USE_TLS=True
   EMAIL_HOST_USER=apikey
   EMAIL_HOST_PASSWORD=your-sendgrid-api-key
   DEFAULT_FROM_EMAIL=noreply@yourdomain.com
   ```

8. **Deploy**: Railway will automatically deploy when you push to main branch

### 3. Post-Deployment

1. **Create Superuser**:
   - Go to Railway dashboard → Your service → Deployments → Latest deployment
   - Click "View Logs" → Open shell
   - Run: `python manage.py createsuperuser`

2. **Access Your App**:
   - Railway provides a URL like: `https://your-app.railway.app`
   - Visit: `https://your-app.railway.app/admin/` for admin panel

### 4. Custom Domain (Optional)

1. In Railway dashboard → Your service → Settings
2. Add custom domain
3. Update `ALLOWED_HOSTS` environment variable

## Environment Variables Summary

| Variable | Required | Description |
|----------|----------|-------------|
| `SECRET_KEY` | Yes | Django secret key |
| `DEBUG` | Yes | Set to `False` for production |
| `ALLOWED_HOSTS` | Yes | Comma-separated hosts |
| `DATABASE_URL` | Auto | Set by Railway PostgreSQL service |
| `USE_LLM` | Yes | Set to `true` to enable LLM (default: `true`) |
| `LLM_PROVIDER` | Yes | Set to `groq` for Groq LLM (default: `groq`) |
| `GROQ_API_KEY` | Yes | Groq API key from https://console.groq.com/ (starts with `gsk_`) |
| `GROQ_MODEL` | No | Groq model name (default: `llama-3.3-70b-versatile`) |
| `EMAIL_HOST` | No | SMTP server for emails |
| `EMAIL_PORT` | No | SMTP port (usually 587) |
| `EMAIL_USE_TLS` | No | Set to `True` |
| `EMAIL_HOST_USER` | No | Email username/API key |
| `EMAIL_HOST_PASSWORD` | No | Email password/API key |
| `DEFAULT_FROM_EMAIL` | No | Sender email address |

## Troubleshooting

**Migrations not running?**
- Check Railway logs
- Manually run: `python manage.py migrate` in Railway shell

**Static files not loading?**
- Railway automatically runs `collectstatic` via Procfile
- Check that `STATIC_ROOT` is set correctly

**Database connection issues?**
- Verify `DATABASE_URL` is set (Railway sets this automatically)
- Check PostgreSQL service is running

**Email not sending?**
- Verify email environment variables are set
- Check email service logs
- For development, emails print to console logs

## Support

For issues, check:
- Railway logs in dashboard
- Django logs in application
- Environment variables are correctly set


