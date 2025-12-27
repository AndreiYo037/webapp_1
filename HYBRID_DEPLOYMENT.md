# Hybrid Deployment Guide - App on Cloud + Ollama Separate

## How It Works

1. **Deploy your Django app** to Railway/Render (free cloud hosting)
2. **Run Ollama separately** on:
   - Your local computer (with ngrok/Cloudflare Tunnel)
   - A small VPS ($5/month)
   - Another server you control
3. **Connect them** via the `OLLAMA_BASE_URL` setting

## Option 1: Ollama on Your Local Computer

### Step 1: Make Ollama Accessible

**Using ngrok (Easiest):**
```bash
# Install ngrok: https://ngrok.com
ngrok http 11434

# You'll get a URL like: https://abc123.ngrok.io
```

**Using Cloudflare Tunnel (Free, More Permanent):**
```bash
# Install cloudflared
# Create tunnel
cloudflared tunnel --url http://localhost:11434
```

### Step 2: Deploy App to Cloud

Deploy to Railway/Render as normal.

### Step 3: Set Environment Variables

In your cloud app's environment variables:
```env
OLLAMA_BASE_URL=https://your-ngrok-url.ngrok.io
# Or your Cloudflare tunnel URL
LLM_PROVIDER=ollama
OLLAMA_MODEL=mistral
USE_LLM=true
```

**Note**: Your computer needs to be on for Ollama to work!

---

## Option 2: Ollama on a Separate VPS (Recommended)

### Step 1: Get a VPS

**Recommended**: DigitalOcean Droplet ($5/month)
- 1GB RAM minimum (2GB+ recommended)
- Ubuntu 22.04

### Step 2: Install Ollama on VPS

```bash
# SSH into your VPS
ssh root@your-vps-ip

# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Download a model
ollama pull mistral

# Make Ollama accessible (with security!)
# Option A: Use nginx reverse proxy with SSL
# Option B: Use Cloudflare Tunnel
# Option C: Use ngrok (for testing)
```

### Step 3: Secure Ollama

**Important**: Don't expose Ollama directly to the internet without security!

**Option A: Nginx Reverse Proxy (Recommended)**
```nginx
# /etc/nginx/sites-available/ollama
server {
    listen 443 ssl;
    server_name ollama.yourdomain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://localhost:11434;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

**Option B: Cloudflare Tunnel (Easier, Free)**
```bash
# On your VPS
cloudflared tunnel --url http://localhost:11434
# Get the URL and use it
```

### Step 4: Configure Your Deployed App

In Railway/Render environment variables:
```env
OLLAMA_BASE_URL=https://ollama.yourdomain.com
# Or your Cloudflare tunnel URL
LLM_PROVIDER=ollama
OLLAMA_MODEL=mistral
USE_LLM=true
```

---

## Option 3: Self-Host Everything (VPS)

Deploy both app and Ollama on the same VPS:

### Step 1: Get VPS ($5-10/month)

### Step 2: Install Everything

```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh
ollama pull mistral

# Install Python, Django, etc.
apt update
apt install python3-pip python3-venv nginx

# Clone your app
git clone your-repo
cd flashcard-app

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with production values

# Run migrations
python manage.py migrate
python manage.py collectstatic --noinput

# Set up Gunicorn
gunicorn flashcard_app.wsgi --bind 0.0.0.0:8000
```

### Step 3: Configure Nginx

```nginx
server {
    listen 80;
    server_name yourdomain.com;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Step 4: Set Environment Variables

```env
OLLAMA_BASE_URL=http://localhost:11434
LLM_PROVIDER=ollama
OLLAMA_MODEL=mistral
USE_LLM=true
```

---

## Current App Configuration

Your app **already supports** remote Ollama! 

The `OLLAMA_BASE_URL` setting can be:
- `http://localhost:11434` (local)
- `https://your-ollama-server.com` (remote)
- `https://abc123.ngrok.io` (tunnel)

Just set it in your environment variables!

---

## Quick Comparison

| Approach | Cost | Complexity | Ollama Works? | Best For |
|----------|------|------------|--------------|----------|
| **Cloud + Local Ollama** | Free | Easy | ✅ Yes* | Testing |
| **Cloud + VPS Ollama** | $5/mo | Medium | ✅ Yes | Production |
| **Everything on VPS** | $5-10/mo | Medium | ✅ Yes | Full control |
| **Cloud Only** | Free | Easy | ❌ No | Simple deploy |

*Requires your computer to be on

---

## My Recommendation

**For production use:**
1. Deploy app to Railway/Render (free, easy)
2. Get a small VPS for Ollama ($5/month)
3. Set up Cloudflare Tunnel (free, secure)
4. Connect them via `OLLAMA_BASE_URL`

**For testing:**
1. Deploy app to Railway/Render
2. Run Ollama locally with ngrok
3. Test it out!

**For simplicity:**
1. Deploy app to Railway/Render
2. Use rule-based generation (no Ollama needed)
3. Add Ollama later if needed

---

## Security Notes

⚠️ **Important**: If exposing Ollama to the internet:
- Use HTTPS (SSL certificate)
- Consider authentication
- Use Cloudflare Tunnel (easiest secure option)
- Restrict access by IP if possible
- Don't expose it without security!

---

## Need Help?

I can help you:
- Set up a VPS with Ollama
- Configure Cloudflare Tunnel
- Set up nginx reverse proxy
- Deploy everything to one VPS

Just let me know which approach you prefer! 🚀


