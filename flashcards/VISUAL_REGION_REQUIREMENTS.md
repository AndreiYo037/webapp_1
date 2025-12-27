# Visual Region Detection Requirements

This document lists the optional dependencies for the intelligent visual region detection feature.

## Required Dependencies

The following packages are required for full functionality:

```bash
pip install PyMuPDF  # For PDF layout analysis
pip install opencv-python  # For image processing and region detection
pip install sentence-transformers  # For semantic embeddings
pip install scikit-learn  # For cosine similarity (optional, has fallback)
pip install pytesseract  # For OCR text extraction from regions
```

## Installation

Install all dependencies at once:

```bash
pip install PyMuPDF opencv-python sentence-transformers scikit-learn pytesseract
```

## Feature Description

The visual region detection pipeline:

1. **Detects visual regions** in PDF/Word documents:
   - Graphs and charts
   - Tables
   - Diagrams
   - Formulas
   - Bullet point clusters

2. **Uses layout-aware parsing**:
   - PyMuPDF for PDF block detection
   - OpenCV for contour and line detection
   - Bounding box analysis

3. **Semantic matching**:
   - Extracts text from regions using OCR
   - Generates embeddings using sentence-transformers
   - Matches questions to regions using cosine similarity

4. **Intelligent cropping**:
   - Only crops regions with confidence >= 0.3
   - Saves cropped regions to flashcard `cropped_image` field
   - One region per flashcard maximum

## Fallback Behavior

If dependencies are missing:
- Falls back to standard image extraction
- Uses full page images instead of cropped regions
- Still works but without intelligent region detection

## Configuration

You can configure the embedding model in Django settings:

```python
# settings.py
EMBEDDING_MODEL = 'all-MiniLM-L6-v2'  # Default lightweight model
```

Available models:
- `all-MiniLM-L6-v2` (default, fast, 80MB)
- `all-mpnet-base-v2` (better quality, slower, 420MB)
- `paraphrase-multilingual-MiniLM-L12-v2` (multilingual support)

