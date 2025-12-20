# 🎉 Free LLM Setup with Ollama

## ✅ You're All Set!

Your app is now configured to use **Ollama** - a completely FREE, local LLM that runs on your machine!

## Quick Start (3 Steps)

### Step 1: Make sure Ollama is running
```bash
# Check if Ollama is running
ollama serve

# If it's not running, start it in a separate terminal
# It will run in the background
```

### Step 2: Verify you have a model
You already have `mistral` installed! ✅

To see all models:
```bash
ollama list
```

To download more models (optional):
```bash
ollama pull llama3      # Meta's latest model (recommended)
ollama pull gemma       # Google's model
ollama pull phi         # Microsoft's small model
```

### Step 3: Create .env file (if you haven't already)
```bash
copy .env.example .env
```

Your `.env` should have:
```env
LLM_PROVIDER=ollama
OLLAMA_MODEL=mistral
USE_LLM=true
```

That's it! No API keys needed! 🎉

## How It Works

1. **Upload a file** → Text is extracted
2. **Ollama processes it** → Uses your local `mistral` model
3. **High-quality flashcards generated** → Completely free!

## Available Models

You can change the model in your `.env` file:

| Model | Size | Speed | Quality | Best For |
|-------|------|-------|---------|----------|
| `mistral` | 4.4GB | Fast | Good | ✅ You have this! |
| `llama3` | 4.7GB | Fast | Excellent | Recommended |
| `gemma:2b` | 1.4GB | Very Fast | Good | Low RAM systems |
| `phi` | 1.6GB | Very Fast | Good | Quick generation |
| `qwen` | 4.4GB | Fast | Good | Multilingual |

To switch models:
1. Download: `ollama pull llama3`
2. Update `.env`: `OLLAMA_MODEL=llama3`
3. Restart server

## Troubleshooting

### "Connection refused" error
- Make sure Ollama is running: `ollama serve`
- Check it's on port 11434: `http://localhost:11434`

### Model not found
- List models: `ollama list`
- Download model: `ollama pull mistral`

### Slow generation
- Try a smaller model: `ollama pull gemma:2b`
- Or use `phi` model

### Want to disable LLM?
Just change in `.env`:
```env
LLM_PROVIDER=none
USE_LLM=false
```

## Benefits of Ollama

✅ **100% Free** - No costs, ever!
✅ **Privacy** - Everything runs locally
✅ **No API limits** - Generate as many flashcards as you want
✅ **Works offline** - No internet needed after setup
✅ **Fast** - Runs on your machine
✅ **No API keys** - Just works!

## Test It!

1. Make sure Ollama is running
2. Restart your Django server
3. Upload a file
4. See the magic! ✨

Your flashcards will now be generated using AI - completely free!

