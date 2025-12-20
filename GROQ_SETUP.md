# 🚀 Groq Setup Guide - Free Cloud LLM

## ✅ Groq is Now Integrated!

Your app now uses **Groq** by default - a free, cloud-based LLM that works perfectly on all cloud platforms!

## Why Groq?

✅ **100% Free** - Generous free tier
✅ **Very Fast** - Extremely fast inference
✅ **Works on Cloud** - No local installation needed
✅ **Perfect for Deployment** - Works on Railway, Render, Heroku, etc.
✅ **Multiple Models** - Llama, Mixtral, Gemma available

## Quick Setup (3 Steps)

### Step 1: Get Your Free API Key

1. Go to https://console.groq.com
2. Sign up (free, no credit card needed)
3. Navigate to **API Keys** section
4. Click **"Create API Key"**
5. Copy your key (you won't see it again!)

### Step 2: Add API Key to Your App

**For Local Development:**
```bash
# Create .env file
copy .env.example .env

# Edit .env and add:
GROQ_API_KEY=your-actual-api-key-here
LLM_PROVIDER=groq
```

**For Cloud Deployment (Railway/Render):**
Add as environment variable:
```
GROQ_API_KEY=your-actual-api-key-here
LLM_PROVIDER=groq
```

### Step 3: That's It!

Restart your server and Groq will automatically be used for flashcard generation!

## Available Models

| Model | Description | Best For |
|-------|-------------|----------|
| `llama-3.3-70b-versatile` | Latest Llama, high quality | ✅ Default - Recommended |
| `mixtral-8x7b-32768` | Mixtral, large context | Long documents |
| `gemma2-9b-it` | Google's Gemma | Fast generation |
| `llama-3.1-8b-instant` | Smaller, faster | Quick responses |

Change model in `.env`:
```env
GROQ_MODEL=llama-3.3-70b-versatile
```

## Configuration

Your `.env` file should have:
```env
LLM_PROVIDER=groq
GROQ_API_KEY=your-api-key-here
GROQ_MODEL=llama-3.3-70b-versatile
USE_LLM=true
```

## Free Tier Limits

Groq's free tier is very generous:
- **30 requests per minute**
- **14,400 requests per day**
- **No credit card required**
- **No expiration** (as of 2025)

This is more than enough for a flashcard app!

## How It Works

1. **User uploads file** → Text extracted
2. **Groq API called** → Fast AI processing
3. **High-quality flashcards generated** → Completely free!
4. **Falls back to rule-based** → If API fails or limit reached

## Testing

1. Get your API key
2. Add to `.env` file
3. Restart server
4. Upload a file
5. See AI-generated flashcards! ✨

## Deployment

Groq works perfectly on:
- ✅ Railway
- ✅ Render
- ✅ Heroku
- ✅ PythonAnywhere
- ✅ Any cloud platform!

Just add `GROQ_API_KEY` as an environment variable!

## Troubleshooting

### "API key not found"
- Make sure `GROQ_API_KEY` is set in `.env` or environment variables
- Check for typos in the key

### "Rate limit exceeded"
- Free tier: 30 requests/minute
- App will automatically fall back to rule-based generation
- Wait a minute and try again

### "Model not found"
- Check `GROQ_MODEL` is set correctly
- Use one of the available models listed above

## Comparison: Groq vs Ollama

| Feature | Groq | Ollama |
|---------|------|--------|
| **Cost** | Free | Free |
| **Location** | Cloud | Local |
| **Works on Cloud** | ✅ Yes | ❌ No |
| **Speed** | Very Fast | Fast |
| **Setup** | API Key | Install software |
| **Best For** | Cloud deployment | Local/VPS |

## Next Steps

1. Get your Groq API key
2. Add it to your app
3. Deploy to cloud (Railway/Render)
4. Enjoy free AI-powered flashcards! 🎉

Your app is now ready for cloud deployment with AI features! 🚀

