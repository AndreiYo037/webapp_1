# 🔧 Troubleshoot: Railway Still Shows "Rule-based"

If your Railway app still shows "Rule-based" after setting variables, follow these steps:

## ✅ Step 1: Verify Variables Are Set

1. Go to **Railway Dashboard** → Your Service → **Variables** tab
2. Check these variables exist and have correct values:

```
LLM_PROVIDER = groq
GROQ_API_KEY = your-groq-api-key-here
USE_LLM = true
```

**Important Checks:**
- ✅ No extra spaces before/after values
- ✅ `USE_LLM` is exactly `true` (not `True`, `TRUE`, or `"true"`)
- ✅ `LLM_PROVIDER` is exactly `groq` (lowercase)
- ✅ `GROQ_API_KEY` starts with `gsk_` and has no spaces

## ✅ Step 2: Force Redeploy

After setting variables:
1. Go to **Railway Dashboard** → Your Service
2. Click **"Deployments"** tab
3. Click **"Redeploy"** or **"Deploy"** button
4. Wait for deployment to complete (2-3 minutes)

## ✅ Step 3: Check Railway Logs

1. Go to **Railway Dashboard** → Your Service → **Logs** tab
2. Look for these messages when the app starts:

```
[INFO] Using Groq LLM: llama-3.3-70b-versatile for flashcard generation
```

If you see:
```
[WARNING] Groq API key not found - falling back to rule-based generation
```

Then `GROQ_API_KEY` is not being read correctly.

## ✅ Step 4: Check Header Badge Message

The header badge will show different messages:

- ✅ **"🚀 Groq (llama-3.3-70b-versatile)"** = Working correctly!
- ❌ **"Rule-based (Groq API key missing)"** = `GROQ_API_KEY` not set
- ❌ **"Rule-based (USE_LLM=false)"** = `USE_LLM` is false or not set
- ❌ **"Rule-based (Groq not configured)"** = General configuration issue

## ✅ Step 5: Test File Upload

1. Upload a test file
2. Check Railway Logs for:
   ```
   [INFO] Attempting to generate X flashcards using Groq (cloud LLM)...
   [SUCCESS] Generated X flashcards using Groq!
   ```

If you see:
```
[INFO] Using rule-based flashcard generation (no LLM)
```

Then LLM is not being used.

## 🔍 Common Issues

### Issue 1: Variables Not Saved
**Solution:** Make sure to click "Save" or "Add" after entering each variable.

### Issue 2: Wrong Variable Names
**Solution:** Variable names are case-sensitive. Must be exactly:
- `LLM_PROVIDER` (not `llm_provider` or `Llm_Provider`)
- `GROQ_API_KEY` (not `groq_api_key`)
- `USE_LLM` (not `use_llm`)

### Issue 3: USE_LLM Set to False
**Solution:** Check if `USE_LLM` is set to `false` or `False`. It must be exactly `true`.

### Issue 4: API Key Has Spaces
**Solution:** Make sure `GROQ_API_KEY` has no leading/trailing spaces. Copy-paste carefully.

### Issue 5: Deployment Not Complete
**Solution:** Wait 2-3 minutes after setting variables. Check deployment status in Railway.

### Issue 6: Cached Page
**Solution:** Hard refresh your browser (Ctrl+F5 or Cmd+Shift+R) to clear cache.

## 🎯 Quick Test

After setting variables, check Railway Logs for this exact message when app starts:
```
[INFO] Using Groq LLM: llama-3.3-70b-versatile for flashcard generation
```

If you see this, Groq is configured correctly!

## 📝 Still Not Working?

1. **Double-check all 3 variables** are set correctly
2. **Redeploy** the service manually
3. **Check logs** for error messages
4. **Verify API key** is valid at https://console.groq.com/keys
5. **Try setting variables again** - sometimes Railway needs a refresh

**The most common issue is `USE_LLM` not being set to `true`!**

