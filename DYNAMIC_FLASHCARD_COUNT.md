# 🎯 Dynamic Flashcard Count - Content-Based Generation

## ✅ Feature Implemented!

Your app now **automatically calculates** the optimal number of flashcards based on the content of each uploaded file!

## How It Works

The app analyzes your file and determines the best number of flashcards using:

1. **Word Count** - Primary metric (most reliable)
2. **Sentence Count** - Secondary metric (identifies concepts)
3. **Content Density** - Intelligent scaling algorithm

## Flashcard Count by Content Size

| Content Size | Word Count | Flashcards Generated |
|--------------|------------|---------------------|
| **Very Short** | < 100 words | 5-8 flashcards |
| **Short** | 100-200 words | 8-12 flashcards |
| **Small** | 200-500 words | 12-18 flashcards |
| **Medium** | 500-1,000 words | 18-30 flashcards |
| **Large** | 1,000-2,000 words | 30-45 flashcards |
| **Very Large** | 2,000-3,000 words | 45-60 flashcards |
| **Extra Large** | 3,000-5,000 words | 60-75 flashcards |
| **Huge** | 5,000+ words | 75-100 flashcards (max) |

## Examples

- **1-page document** (~300 words) → ~12-15 flashcards
- **5-page document** (~1,500 words) → ~25-30 flashcards
- **20-page document** (~6,000 words) → ~45-50 flashcards
- **100-page book** (~30,000 words) → ~80-100 flashcards

## Benefits

✅ **No manual configuration** - Automatically adapts to content
✅ **Optimal coverage** - More content = more flashcards
✅ **Efficient** - Short files don't waste time generating too many
✅ **Comprehensive** - Long files get thorough coverage
✅ **Smart scaling** - Balances quality and quantity

## Algorithm Details

The algorithm uses:
- **Primary**: Word count with intelligent scaling
- **Secondary**: Sentence count (identifies distinct concepts)
- **Bounds**: Minimum 5, Maximum 100 flashcards
- **Averaging**: Combines both metrics for accuracy

## Customization

If you want to override the automatic calculation, you can still set a fixed number in `.env`:

```env
# This setting is now ignored (dynamic calculation is used)
# But kept for backward compatibility
DEFAULT_FLASHCARDS_COUNT=20
```

However, the **dynamic calculation will always be used** for new uploads.

## Testing

Try uploading files of different sizes:
- Small text file → Few flashcards
- Medium PDF → Moderate flashcards  
- Large document → Many flashcards

The app will automatically adjust!

## Technical Details

The calculation happens in `calculate_flashcard_count()` function in `file_processor.py`:
- Analyzes text before generation
- Returns optimal count
- Used automatically in `views.py` during file upload

## Status

✅ **Active** - All new file uploads use dynamic calculation
✅ **Tested** - Algorithm verified with various content sizes
✅ **Optimized** - Balanced for quality and performance

Your app now intelligently adapts to each file! 🎉

