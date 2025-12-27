# ✨ Gemini LLM Setup Guide

## What is Gemini?

Google Gemini is a free, cloud-based AI model that you can use for flashcard generation. It's a great alternative to Groq!

## Get Your API Key

1. **Go to**: https://aistudio.google.com/apikey
2. **Sign in** with your Google account
3. **Click** "Create API Key"
4. **Copy** your API key (starts with `AIza...`)

## Setup in Railway/Render

### Environment Variables:

```
LLM_PROVIDER=gemini
GEMINI_API_KEY=your-api-key-here
GEMINI_MODEL=gemini-1.5-flash
USE_LLM=true
```

## Available Models

- **gemini-1.5-flash** (Recommended)
  - Fast and free
  - Good for flashcard generation
  - Free tier available

- **gemini-1.5-pro**
  - More capable
  - May have stricter rate limits
  - Better for complex content

## Features

✅ **Same quality filtering** as Groq
✅ **Automatic fallback** to Groq if Gemini fails
✅ **Comprehensive flashcards** with detailed answers
✅ **Shows status** in header badge (✨ icon)

## How It Works

1. **Set LLM_PROVIDER=gemini** in environment variables
2. **Set GEMINI_API_KEY** with your API key
3. **Upload a file** - Gemini will generate flashcards
4. **If Gemini fails** - automatically tries Groq, then rule-based

## Free Tier Limits

Gemini free tier typically includes:
- Generous free usage
- Rate limits may apply
- Check Google AI Studio for current limits

## Switching Between LLMs

You can easily switch:

**Use Gemini:**
```
LLM_PROVIDER=gemini
GEMINI_API_KEY=your-key
```

**Use Groq:**
```
LLM_PROVIDER=groq
GROQ_API_KEY=your-key
```

**Use Ollama (local):**
```
LLM_PROVIDER=ollama
```

## Troubleshooting

### "Gemini API key invalid"
- Verify key in environment variables
- Get new key from https://aistudio.google.com/apikey
- Make sure no extra spaces

### "Gemini quota exceeded"
- Check Google AI Studio dashboard
- Wait for quota reset
- Consider using Groq as alternative

### Gemini not working
- Check logs for specific error
- Verify API key is set correctly
- App will automatically fallback to Groq

## Benefits of Gemini

- ✅ Free tier available
- ✅ Cloud-based (works on Railway, Render, etc.)
- ✅ High-quality responses
- ✅ Good alternative if Groq quota is exceeded
- ✅ Automatic fallback to other LLMs

**Gemini is now integrated and ready to use!** 🚀


