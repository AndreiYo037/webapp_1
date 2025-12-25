# Enable Semantic Matching for Visual Regions

## Current Status
Your system is working with **fallback matching** (round-robin distribution). This ensures all flashcards get images, but the matching is not semantic.

## To Enable Semantic Matching

Install the missing dependency:

```bash
pip install sentence-transformers
```

## What This Enables

With `sentence-transformers` installed:
- **Semantic matching**: Questions are matched to regions based on meaning, not just position
- **Better accuracy**: Regions that actually relate to the question content are selected
- **Intelligent selection**: Uses embeddings to find the most relevant visual region for each question

## Current Behavior (Fallback)

Without `sentence-transformers`:
- ✅ Still works - all flashcards get images
- ✅ Uses round-robin distribution (question 1 → region 1, question 2 → region 2, etc.)
- ⚠️ Matching is positional, not semantic

## Optional: Install All Dependencies

For full functionality, install all optional dependencies:

```bash
pip install sentence-transformers scikit-learn opencv-python PyMuPDF pytesseract
```

## After Installation

1. Restart your Django server
2. Re-upload your document
3. You'll see in logs: `[SUCCESS] Embedding model loaded` instead of the warning
4. Matching will be semantic instead of round-robin

