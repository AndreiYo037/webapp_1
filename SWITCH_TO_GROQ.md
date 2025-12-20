# 🚀 Switch to Groq LLM

## Quick Setup

**In Railway/Render Environment Variables, set:**

```
LLM_PROVIDER=groq
GROQ_API_KEY=your-groq-api-key-here
GROQ_MODEL=llama-3.3-70b-versatile
USE_LLM=true
```

## Steps

1. **Go to Railway Dashboard** → Your Service → Variables
2. **Set or update:**
   - `LLM_PROVIDER=groq`
   - `GROQ_API_KEY=your-api-key` (get from https://console.groq.com/keys)
   - `GROQ_MODEL=llama-3.3-70b-versatile` (optional, has default)
   - `USE_LLM=true`
3. **Save** - Railway will auto-redeploy
4. **Verify** - Check header badge shows "🚀 Groq (model)"

## Verify It's Working

**Check Railway Logs:**
- Look for: `[INFO] Attempting to generate X flashcards using Groq (cloud LLM)...`
- Should see: `[SUCCESS] Generated X flashcards using Groq!`

**Check Header Badge:**
- Should show: "🚀 Groq (llama-3.3-70b-versatile)"

## Default Behavior

The app **defaults to Groq** if `LLM_PROVIDER` is not set, so you're already using Groq by default!

## If Not Working

1. **Verify API key** is set correctly
2. **Check logs** for Groq errors
3. **Make sure** `USE_LLM=true`
4. **Verify** `LLM_PROVIDER=groq` (not `ollama` or `gemini`)

**Groq is now the default and will be used automatically!** 🚀

