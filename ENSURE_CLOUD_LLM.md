# ☁️ Ensure Cloud LLM Runs in Deployment

## Quick Answer

**Set these environment variables in Railway/Render:**

```
LLM_PROVIDER=groq
GROQ_API_KEY=your-groq-api-key
USE_LLM=true
```

**OR use Gemini:**

```
LLM_PROVIDER=gemini
GEMINI_API_KEY=your-gemini-api-key
USE_LLM=true
```

## Cloud LLM Options

### Option 1: Groq (Recommended for Deployment)
- ✅ **Free tier available**
- ✅ **Works on all cloud platforms** (Railway, Render, etc.)
- ✅ **Very fast**
- ✅ **No local installation needed**

**Setup:**
```
LLM_PROVIDER=groq
GROQ_API_KEY=your-api-key
GROQ_MODEL=llama-3.3-70b-versatile
```

### Option 2: Gemini (Google AI)
- ✅ **Free tier available**
- ✅ **Works on all cloud platforms**
- ✅ **High quality**
- ✅ **No local installation needed**

**Setup:**
```
LLM_PROVIDER=gemini
GEMINI_API_KEY=your-api-key
GEMINI_MODEL=gemini-1.5-flash
```

## ❌ DO NOT Use in Deployment

### Ollama (Local Only)
- ❌ **Requires local installation**
- ❌ **Won't work on Railway/Render**
- ❌ **Only works on your own server**

**If you see `LLM_PROVIDER=ollama` in production, change it!**

## How to Verify Cloud LLM is Running

### 1. Check Environment Variables

**In Railway:**
- Dashboard → Your Service → Variables
- Verify:
  - `LLM_PROVIDER=groq` OR `LLM_PROVIDER=gemini`
  - `GROQ_API_KEY` or `GEMINI_API_KEY` is set
  - `USE_LLM=true`

**In Render:**
- Dashboard → Your Service → Environment
- Same variables as above

### 2. Check Header Badge

The app header shows which LLM is active:
- **🚀 Groq (model)** = Cloud LLM working
- **✨ Gemini (model)** = Cloud LLM working
- **🖥️ Ollama (model)** = Local LLM (won't work in cloud!)
- **📝 Rule-based** = No LLM (fallback)

### 3. Check Logs

**Railway:**
- Service → Deployments → Latest → View Logs
- Look for:
  - `[INFO] Using Groq LLM: ...` ✅
  - `[INFO] Using Gemini LLM: ...` ✅
  - `[SUCCESS] Generated X flashcards using Groq!` ✅
  - `[SUCCESS] Generated X flashcards using Gemini!` ✅

**Render:**
- Service → Logs tab
- Same messages as above

## Default Configuration

The app defaults to **Groq** (cloud-based) if no provider is specified:

```python
LLM_PROVIDER = os.getenv('LLM_PROVIDER', 'groq').lower()  # Defaults to Groq!
```

So if you don't set `LLM_PROVIDER`, it will use Groq (cloud) by default.

## Fallback Behavior

The app has smart fallback:

1. **Tries configured provider first** (Groq/Gemini/Ollama)
2. **If Gemini fails** → Tries Groq
3. **If Groq fails** → Tries Gemini (if configured)
4. **If all fail** → Falls back to rule-based

This ensures cloud LLMs are tried before falling back.

## Production Checklist

Before deploying, ensure:

- [ ] `LLM_PROVIDER=groq` OR `LLM_PROVIDER=gemini` (NOT ollama)
- [ ] `GROQ_API_KEY` or `GEMINI_API_KEY` is set
- [ ] `USE_LLM=true`
- [ ] `DEBUG=False` (for production)
- [ ] `ALLOWED_HOSTS` includes your domain

## Quick Setup for Railway

**Minimal cloud LLM setup:**

```
LLM_PROVIDER=groq
GROQ_API_KEY=your-groq-api-key
USE_LLM=true
```

That's it! Groq will be used automatically.

## Troubleshooting

### "Ollama connection failed" in logs
→ You have `LLM_PROVIDER=ollama` set. Change to `groq` or `gemini`.

### "Rule-based generation" in logs
→ Cloud LLM not configured. Set `GROQ_API_KEY` or `GEMINI_API_KEY`.

### Badge shows "Ollama" in production
→ Change `LLM_PROVIDER` to `groq` or `gemini` in environment variables.

## Summary

**To ensure cloud LLM runs:**
1. Set `LLM_PROVIDER=groq` or `LLM_PROVIDER=gemini`
2. Set the corresponding API key
3. Set `USE_LLM=true`
4. **Never set `LLM_PROVIDER=ollama` in production!**

**The app defaults to Groq (cloud) if nothing is set, so you're safe!** ☁️


