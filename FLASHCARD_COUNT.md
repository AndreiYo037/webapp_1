# 📊 Flashcard Count Configuration

## What Changed

Previously, the app was hardcoded to generate **15 flashcards** per file. Now it's **configurable**!

## Current Setting

**Default**: **20 flashcards** per file (increased from 15)

## How to Change It

### Option 1: Edit `.env` File

Open your `.env` file and change:
```env
DEFAULT_FLASHCARDS_COUNT=20
```

Change `20` to any number you want:
- `10` - Fewer flashcards (faster generation)
- `20` - Default (balanced)
- `30` - More flashcards (better coverage)
- `50` - Many flashcards (comprehensive)
- `100` - Maximum coverage

### Option 2: Environment Variable

For cloud deployment, add to your platform's environment variables:
```
DEFAULT_FLASHCARDS_COUNT=30
```

## Recommendations

| Content Size | Recommended Count |
|--------------|-------------------|
| Short (1-2 pages) | 10-15 flashcards |
| Medium (3-10 pages) | 20-30 flashcards |
| Long (10+ pages) | 30-50 flashcards |
| Very Long (50+ pages) | 50-100 flashcards |

## Notes

- **Groq Free Tier**: 30 requests/minute, 14,400/day
- **Generation Time**: More flashcards = longer generation time
- **Quality**: Groq generates high-quality flashcards regardless of count
- **Content**: The number generated depends on available content in your file

## After Changing

1. **Restart your server** for changes to take effect
2. **Upload a new file** to see the new count
3. **Existing flashcards** won't change - only new uploads

## Example

To generate 30 flashcards per file:
```env
DEFAULT_FLASHCARDS_COUNT=30
```

Then restart server and upload a file!

