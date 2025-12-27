# Visual Region Display Features and Confidence Thresholds

## Overview
This document describes all features related to displaying visual regions of images and the quality/confidence thresholds that prevent low-quality images from being displayed.

---

## 1. Visual Region Detection Quality Filters

### Location: `visual_region_service.py` - `VisualRegionDetector._create_region_from_bbox()`

**Feature: Size-Based Filtering**
- **Minimum Size**: Regions must be at least **150x100 pixels** after expansion
- **Maximum Size**: Regions covering more than **80% of page area** are rejected (likely entire page)
- **Code Reference**: Lines 308-334
```python
# Reject regions that are still too small after expansion
if cropped.width < 150 or cropped.height < 100:
    print(f"[DEBUG] Rejected region too small: {cropped.width}x{cropped.height} (minimum: 150x100)")
    return None
```

**Feature: Blank/White Region Detection**
- **White Pixel Threshold**: Regions with **>95% white pixels** are rejected
- **Variance Threshold**: Regions with **variance < 100** are rejected (too uniform/blank)
- **Code Reference**: Lines 336-361
```python
# Reject if image is >95% white OR has very low variance (<100)
if white_ratio > 0.95 or variance < 100:
    print(f"[DEBUG] Rejected blank/white region...")
    return None
```

**Feature: Region Size Ratio Filtering**
- **Page Coverage Limit**: Regions covering **>80% of page** are rejected
- **Dimension Check**: Regions with width/height **>95% of page dimensions** are rejected
- **Code Reference**: Lines 284-300
```python
if region_ratio > 0.80:
    print(f"[DEBUG] Rejected region covering {region_ratio*100:.1f}% of page (too large, likely entire page)")
    return None
```

---

## 2. Semantic Matching Confidence Thresholds

### Location: `visual_region_service.py` - `SemanticMatcher.match_regions_to_questions()`

**Feature: Minimum Confidence Threshold**
- **Default Threshold**: `min_confidence = 0.25` (25% similarity required)
- **Purpose**: Only matches with similarity score **≥ 0.25** are returned
- **Code Reference**: Line 474, 588, 717
```python
def match_regions_to_questions(self, regions: List[VisualRegion], 
                              questions: List[str],
                              min_confidence: float = 0.25) -> List[Tuple[int, int, float]]:
```

**Feature: Dynamic Threshold Adjustment**
- **Auto-Adjustment**: If all scores are between **0.20 and 0.25**, threshold is adjusted to **90% of max score** (but not below 0.20)
- **Very Low Scores**: If max score **≤ 0.20**, no matches are displayed (warning logged)
- **Code Reference**: Lines 575-583
```python
if max_scores and max(max_scores) < min_confidence and max(max_scores) > 0.20:
    adjusted_threshold = max(0.20, max(max_scores) * 0.90)
    min_confidence = adjusted_threshold
elif max_scores and max(max_scores) <= 0.20:
    print(f"[WARNING] All similarity scores are very low (max: {max(max_scores):.3f}), no matches will be displayed")
```

**Feature: No Display on Low Confidence**
- **Behavior**: If no matches found above threshold, **no images are displayed**
- **Code Reference**: Lines 604-607
```python
if not matches:
    print(f"[WARNING] No matches found above threshold {min_confidence}")
    print("[INFO] No images will be displayed - semantic matching failed")
    return []
```

---

## 3. Quality-Based Region Selection

### Location: `visual_region_service.py` - `SemanticMatcher.match_regions_to_questions()` and `VisualRegionPipeline.process_document()`

**Feature: Top Quality Region Selection**
- **Limit**: Only top **30 regions** (sorted by confidence) are processed for matching
- **Purpose**: Faster processing while maintaining quality
- **Code Reference**: Lines 489-495, 704-710
```python
MAX_SAFE_PROCESSING = 30
if len(regions) > MAX_SAFE_PROCESSING:
    # Sort by confidence and take top regions for better quality
    regions = sorted(regions, key=lambda r: r.confidence, reverse=True)[:MAX_SAFE_PROCESSING]
```

**Feature: Confidence-Based Region Scoring**
- **Calculation**: Confidence = `min(1.0, area / (page_area * 0.3))`
- **Meaning**: Max confidence (1.0) if region covers **>30% of page**
- **Code Reference**: Line 365
```python
confidence = min(1.0, area / (page_image.width * page_image.height * 0.3))
```

---

## 4. Image Display Logic

### Location: `views.py` - `upload_file()` and `templates/flashcards/view_flashcards.html`

**Feature: Conditional Image Display**
- **Template Check**: Images are only displayed if `flashcard.cropped_image` exists
- **Code Reference**: `view_flashcards.html` lines 103-107
```html
{% if flashcard.cropped_image %}
<div class="image-container">
    <img src="{{ flashcard.cropped_image.url }}" alt="Flashcard image">
</div>
{% endif %}
```

**Feature: Image Saving Only on Match**
- **Behavior**: Images are only saved to flashcards if they pass semantic matching
- **Code Reference**: `views.py` lines 248-280
```python
# Add cropped image if matched
if image_matches and idx in image_matches:
    region = image_matches[idx]
    if region and region.image:
        # Save cropped image...
```

---

## 5. Error Handling and Fallbacks

### Location: `visual_region_service.py` - Multiple locations

**Feature: No Images on Matching Failure**
- **Behavior**: If semantic matching fails (memory errors, model unavailable, etc.), **no images are displayed**
- **Code Reference**: Lines 484, 537, 543, 606, 614, 720, 726
```python
print("[WARNING] Embedding model not available, no images will be displayed - semantic matching failed")
print("[INFO] No images will be displayed - semantic matching failed")
```

**Feature: Quality Preservation in Fallbacks**
- **Behavior**: Even in fallback scenarios, only detected visual regions (not full pages) are used
- **Code Reference**: `views.py` lines 217-223
```python
if all_detected_regions and len(all_detected_regions) > 0:
    # Use detected visual regions (cropped sections) in round-robin
    # These are already quality-filtered regions
```

---

## Summary of Confidence/Quality Thresholds

| Feature | Threshold | Location | Effect |
|---------|-----------|----------|--------|
| **Minimum Region Size** | 150x100px | `_create_region_from_bbox()` | Rejects tiny regions |
| **Maximum Region Size** | 80% of page | `_create_region_from_bbox()` | Rejects full-page regions |
| **White Pixel Ratio** | >95% white | `_create_region_from_bbox()` | Rejects blank regions |
| **Image Variance** | <100 | `_create_region_from_bbox()` | Rejects uniform/blank regions |
| **Semantic Similarity** | ≥0.25 (default) | `match_regions_to_questions()` | Only displays high-confidence matches |
| **Auto-Adjust Threshold** | 0.20-0.25 range | `match_regions_to_questions()` | Adjusts threshold if scores are close |
| **Very Low Score Rejection** | ≤0.20 | `match_regions_to_questions()` | No display if all scores too low |
| **Top Quality Selection** | Top 30 by confidence | `match_regions_to_questions()` | Processes only best regions |

---

## Key Takeaways

1. **Multiple Quality Filters**: Images must pass size, blank detection, and semantic matching filters
2. **Confidence Threshold**: Default 0.25 similarity required, auto-adjusts to 0.20-0.25 range if needed
3. **No Low-Quality Display**: Images below confidence threshold are **never displayed**
4. **Quality Preservation**: Even in fallbacks, only quality-filtered visual regions are used (not full pages)
5. **Error Handling**: Matching failures result in no images displayed (quality over quantity)

---

## Configuration

The confidence threshold can be adjusted in:
- `visual_region_service.py` line 717: `min_confidence=0.25` (in `VisualRegionPipeline.process_document()`)
- `visual_region_service.py` line 474: `min_confidence: float = 0.25` (in `SemanticMatcher.match_regions_to_questions()`)

To change the threshold, modify these values. Higher values (e.g., 0.30, 0.35) will be more strict and display fewer images. Lower values (e.g., 0.20, 0.15) will be more permissive but may include lower-quality matches.

