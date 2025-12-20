# 🚀 Railway Groq LLM Setup Guide

## Problem: LLM showing as "Rule-based" instead of Groq

This happens when the `GROQ_API_KEY` environment variable is not set in Railway.

## ✅ Quick Fix - Set These Variables in Railway

1. **Go to Railway Dashboard** → Your Service → Variables tab

2. **Add/Update these environment variables:**

```
LLM_PROVIDER=groq
GROQ_API_KEY=your-groq-api-key-here
GROQ_MODEL=llama-3.3-70b-versatile
USE_LLM=true
```

3. **Save** - Railway will automatically redeploy

4. **Verify** - After redeploy, check:
   - Header badge should show: "🚀 Groq (llama-3.3-70b-versatile)"
   - Upload a file and check logs for: `[INFO] Attempting to generate X flashcards using Groq (cloud LLM)...`

## 📋 Complete Railway Environment Variables Checklist

Make sure ALL of these are set in Railway:

### Required for Groq:
- ✅ `LLM_PROVIDER=groq`
- ✅ `GROQ_API_KEY=your-api-key-here`
- ✅ `USE_LLM=true`

### Optional (has defaults):
- `GROQ_MODEL=llama-3.3-70b-versatile` (default if not set)

### Django Production Settings:
- `DEBUG=False`
- `SECRET_KEY=your-secret-key-here`
- `ALLOWED_HOSTS=your-railway-domain.railway.app`
- `CSRF_TRUSTED_ORIGINS=https://your-railway-domain.railway.app`

## 🔍 How to Verify It's Working

### 1. Check Header Badge
- Should show: "🚀 Groq (llama-3.3-70b-versatile)"
- Status should be: "active" (green)

### 2. Check Railway Logs
Go to Railway Dashboard → Service → Logs

Look for these messages when uploading a file:
```
[INFO] Attempting to generate X flashcards using Groq (cloud LLM)...
[SUCCESS] Generated X flashcards using Groq!
```

### 3. Test File Upload
- Upload a file
- If Groq is working, you'll see comprehensive flashcards with detailed answers
- If rule-based, you'll see simpler flashcards

## ❌ Common Issues

### Issue: Still showing "Rule-based"
**Solution:** 
- Double-check `GROQ_API_KEY` is set correctly (no extra spaces)
- Make sure `USE_LLM=true` (not `false`)
- Make sure `LLM_PROVIDER=groq` (lowercase)

### Issue: "Groq not configured"
**Solution:**
- `GROQ_API_KEY` is missing or empty
- Add it in Railway Variables

### Issue: API errors in logs
**Solution:**
- Check if API key is valid
- Check Groq dashboard for quota/rate limits
- Verify API key format: should start with `gsk_`

## 🎯 Step-by-Step Railway Setup

1. **Open Railway Dashboard**
   - Go to https://railway.app
   - Select your project
   - Click on your service

2. **Go to Variables Tab**
   - Click "Variables" in the left sidebar
   - Or click "New" → "Variable"

3. **Add Variables One by One:**
   ```
   Name: LLM_PROVIDER
   Value: groq
   ```
   
   ```
   Name: GROQ_API_KEY
   Value: your-groq-api-key-here
   ```
   
   ```
   Name: USE_LLM
   Value: true
   ```

4. **Save and Wait for Redeploy**
   - Railway automatically redeploys when variables change
   - Wait 1-2 minutes for deployment to complete

5. **Test**
   - Visit your Railway URL
   - Check header badge shows Groq
   - Upload a test file

## 📝 Notes

- **Groq is FREE** - No credit card required
- **Get API Key:** https://console.groq.com/keys
- **Default Model:** `llama-3.3-70b-versatile` (fast and capable)
- **Alternative Models:** `mixtral-8x7b-32768`, `gemma2-9b-it`

## ✅ After Setup

Once variables are set correctly:
- Header badge will show Groq
- File uploads will use Groq for flashcard generation
- Logs will confirm Groq usage
- Flashcards will be comprehensive and detailed

**Your Railway app should now use Groq LLM!** 🚀

