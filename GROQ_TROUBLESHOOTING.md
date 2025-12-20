# 🔧 Groq LLM Troubleshooting Guide

## Common Issues

### 1. Out of Tokens/Quota Exceeded

**Symptoms:**
- Error: "quota exceeded" or "rate limit" or HTTP 429
- App falls back to rule-based generation
- LLM badge shows "active" but flashcards are simple

**Solutions:**
- **Check Groq Dashboard**: https://console.groq.com/
  - Go to "Usage" or "Billing" section
  - Check your free tier limits
  - Free tier: Usually 14,400 requests/day or similar limits
  
- **Wait for Reset**: Free tier quotas reset daily
- **Upgrade Account**: If you need more tokens
- **Reduce Usage**: 
  - Upload smaller files
  - Generate fewer flashcards per file
  - The app already reduces flashcard count based on content

### 2. Invalid API Key

**Symptoms:**
- Error: "401 unauthorized" or "invalid API key"
- LLM badge shows "fallback" status

**Solutions:**
- **Verify API Key** in Railway/Render environment variables
- **Get New Key**: https://console.groq.com/keys
- **Check for Typos**: No extra spaces, correct format (starts with `gsk_`)

### 3. Model Not Available

**Symptoms:**
- Error: "model not found" or "invalid model"
- App falls back to rule-based

**Solutions:**
- **Check Model Name**: Default is `llama-3.3-70b-versatile`
- **Available Models**:
  - `llama-3.3-70b-versatile` (default, recommended)
  - `mixtral-8x7b-32768`
  - `gemma2-9b-it`
- **Update GROQ_MODEL** environment variable if needed

### 4. Network/Connection Errors

**Symptoms:**
- Error: "connection timeout" or "network error"
- Intermittent failures

**Solutions:**
- **Check Internet**: Railway/Render should have stable connection
- **Check Groq Status**: https://status.groq.com/
- **Retry**: Usually temporary, try again later

## How to Check What's Happening

### 1. Check Railway/Render Logs

**Railway:**
- Go to Dashboard → Your Service → Deployments
- Click latest deployment → View Logs
- Look for messages like:
  - `[ERROR] Groq quota/rate limit exceeded`
  - `[ERROR] Groq API key invalid`
  - `[SUCCESS] Generated X flashcards using Groq!`

**Render:**
- Go to Dashboard → Your Service → Logs tab
- Same error messages apply

### 2. Check LLM Badge

The badge in the header shows:
- **🚀 Groq (model)** - Active and working
- **📝 Rule-based** - Groq failed, using fallback

### 3. Test with Small File

Upload a small text file to test:
- If it works → Groq is fine, may be quota for larger files
- If it fails → Check error messages in logs

## Error Messages Explained

### `[ERROR] Groq quota/rate limit exceeded`
→ **You've hit your free tier limit**
- Wait for daily reset
- Check Groq dashboard for usage
- Consider upgrading or reducing usage

### `[ERROR] Groq API key invalid`
→ **API key problem**
- Verify key in environment variables
- Get new key from Groq console
- Make sure no extra spaces

### `[ERROR] Groq model not available`
→ **Model name issue**
- Check GROQ_MODEL setting
- Use one of the available models listed above

### `[ERROR] Groq network/connection error`
→ **Network issue**
- Usually temporary
- Check Groq status page
- Retry later

## Free Tier Limits

Groq's free tier typically includes:
- **14,400 requests per day** (or similar)
- **Rate limits** (requests per minute)
- **Token limits** per request

**Note**: Limits may vary, check your Groq dashboard for exact numbers.

## Solutions

### If Out of Tokens:

1. **Wait**: Quotas usually reset daily
2. **Reduce Usage**: 
   - Smaller files generate fewer flashcards
   - The app already optimizes flashcard count
3. **Upgrade**: Consider paid plan if needed
4. **Alternative**: Use Ollama (local, unlimited) if available

### If Still Not Working:

1. **Check Logs**: Look for specific error messages
2. **Verify Settings**: 
   - `LLM_PROVIDER=groq`
   - `GROQ_API_KEY=your-key`
   - `USE_LLM=true`
3. **Test API Key**: Try making a direct API call
4. **Contact Support**: Groq support if persistent issues

## Quick Test

To test if Groq is working:

1. Upload a small text file (< 500 words)
2. Check Railway/Render logs
3. Look for: `[SUCCESS] Generated X flashcards using Groq!`
4. If you see errors, check the specific error message above

**The app will automatically fall back to rule-based generation if Groq fails, so it will still work!**

