"""
Visual Region Detection and Matching Service
Detects visual regions (graphs, tables, diagrams, formulas) in documents
and matches them to flashcard questions using semantic similarity.
"""
import io
import json
from typing import List, Dict, Tuple, Optional
from PIL import Image
import numpy as np
from django.conf import settings

# Try to import optional dependencies
# OpenCV is REQUIRED for visual region detection
try:
    import cv2
    # Verify OpenCV is actually working by checking version
    cv2_version = cv2.__version__
    CV2_AVAILABLE = True
    print(f"[INFO] OpenCV {cv2_version} is available and ready for visual region detection")
except ImportError as e:
    CV2_AVAILABLE = False
    print(f"[ERROR] OpenCV not available - visual region detection will fail!")
    print(f"[ERROR] Import error: {str(e)}")
    print(f"[ERROR] Install with: pip install opencv-python-headless")
except Exception as e:
    CV2_AVAILABLE = False
    print(f"[ERROR] OpenCV import failed: {str(e)}")

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

try:
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


class VisualRegion:
    """Represents a detected visual region in a document"""
    def __init__(self, bbox: Tuple[int, int, int, int], page_num: int, 
                 region_type: str, confidence: float, image: Image.Image = None):
        self.bbox = bbox  # (x0, y0, x1, y1)
        self.page_num = page_num
        self.region_type = region_type  # 'table' (only table regions are used)
        self.confidence = confidence
        self.image = image
        self.embedding = None  # Will be populated for semantic matching


class VisualRegionDetector:
    """Detects visual regions in PDF/Word documents"""
    
    def __init__(self):
        self.min_region_area = 2500  # Lowered from 3000 to detect even more visual regions
        self.aspect_ratio_range = (0.2, 5.0)  # More permissive aspect ratios to catch more regions
        self.max_region_area_ratio = 0.50  # Maximum 50% of page area (stricter than before)
    
    def detect_regions_in_pdf(self, file_path: str) -> List[VisualRegion]:
        """Detect visual regions in a PDF document"""
        if not CV2_AVAILABLE:
            print("[ERROR] OpenCV is required for visual region detection but is not available!")
            print("[ERROR] Please ensure opencv-python-headless is installed: pip install opencv-python-headless")
            return []
        
        regions = []
        try:
            import fitz  # PyMuPDF
            
            doc = fitz.open(file_path)
            
            print(f"[INFO] Processing {len(doc)} pages for visual region detection...")
            for page_num in range(len(doc)):
                page = doc[page_num]
                
                # Get page as image for processing
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x zoom for better quality
                img_data = pix.tobytes("png")
                page_image = Image.open(io.BytesIO(img_data))
                
                # Detect regions on this page
                page_regions = self._detect_regions_on_page(page, page_image, page_num)
                regions.extend(page_regions)
                print(f"[INFO] Page {page_num + 1}/{len(doc)}: Found {len(page_regions)} visual regions (total: {len(regions)})")
            
            doc.close()
            return regions
            
        except ImportError:
            print("[WARNING] PyMuPDF not installed. Install with: pip install PyMuPDF")
            return []
        except Exception as e:
            print(f"[ERROR] Failed to detect regions in PDF: {str(e)}")
            return []
    
    def detect_regions_in_docx(self, file_path: str) -> List[VisualRegion]:
        """Detect visual regions in a Word document"""
        regions = []
        try:
            import zipfile
            from PIL import Image
            
            # Open docx as zip
            docx_zip = zipfile.ZipFile(file_path)
            
            # Get images from media folder
            image_files = [f for f in docx_zip.namelist() 
                          if f.startswith('word/media/') and 
                          any(f.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp'])]
            
            for idx, image_file in enumerate(sorted(image_files)):
                try:
                    image_data = docx_zip.read(image_file)
                    img = Image.open(io.BytesIO(image_data))
                    
                    # Each image in Word is treated as a visual region
                    bbox = (0, 0, img.width, img.height)
                    region = VisualRegion(
                        bbox=bbox,
                        page_num=idx,  # Use index as page number
                        region_type='table',  # Default type
                        confidence=0.8,
                        image=img
                    )
                    regions.append(region)
                except Exception as e:
                    print(f"[WARNING] Failed to process image {image_file}: {str(e)}")
                    continue
            
            docx_zip.close()
            return regions
            
        except Exception as e:
            print(f"[ERROR] Failed to detect regions in Word document: {str(e)}")
            return []
    
    def _detect_regions_on_page(self, page, page_image: Image.Image, page_num: int) -> List[VisualRegion]:
        """Detect visual regions on a single page using layout analysis"""
        regions = []
        
        if not CV2_AVAILABLE:
            # Don't create entire page regions - return empty if OpenCV not available
            print(f"[WARNING] OpenCV not available, cannot detect regions on page {page_num + 1}")
            return []
        
        try:
            
            # Convert PIL to OpenCV format
            img_array = np.array(page_image)
            if len(img_array.shape) == 3:
                gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            else:
                gray = img_array
            
            # Method 1: Detect using PyMuPDF's block detection
            try:
                blocks = page.get_text("dict")["blocks"]
                for block in blocks:
                    if "image" in block:  # Image block
                        bbox = block["bbox"]  # (x0, y0, x1, y1)
                        region = self._create_region_from_bbox(bbox, page_image, page_num, "table")
                        if region:
                            regions.append(region)
            except:
                pass
            
            # Method 2: Detect using contour analysis (for graphs, tables)
            try:
                # Apply threshold
                _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
                
                # Find contours - use RETR_TREE to avoid picking up entire page as one contour
                contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
                
                page_area = gray.shape[1] * gray.shape[0]  # width * height
                
                for contour in contours:
                    x, y, w, h = cv2.boundingRect(contour)
                    area = w * h
                    
                    # Filter by size
                    if area < self.min_region_area:
                        continue
                    
                    # CRITICAL: Reject contours that are too large (likely entire page or large sections)
                    # STRICT: Reject if covering more than 50% of page (reduced from 80%)
                    region_ratio = area / page_area if page_area > 0 else 0
                    if region_ratio > 0.50:  # Reduced from 0.80 to 0.50
                        print(f"[DEBUG] Rejected contour covering {region_ratio*100:.1f}% of page (max 50% allowed)")
                        continue
                    
                    # Check aspect ratio
                    aspect_ratio = w / h if h > 0 else 0
                    if not (self.aspect_ratio_range[0] <= aspect_ratio <= self.aspect_ratio_range[1]):
                        continue
                    
                    # Determine region type based on characteristics
                    region_type = self._classify_region_type(w, h, area, gray[y:y+h, x:x+w])
                    
                    bbox = (x, y, x + w, y + h)
                    region = self._create_region_from_bbox(bbox, page_image, page_num, region_type)
                    if region:
                        regions.append(region)
            except Exception as e:
                print(f"[WARNING] Contour detection failed: {str(e)}")
            
            # Method 3: Detect tables using horizontal/vertical lines
            try:
                table_regions = self._detect_tables(gray, page_image, page_num)
                regions.extend(table_regions)
            except Exception as e:
                print(f"[WARNING] Table detection failed: {str(e)}")
            
            return regions
            
        except Exception as e:
            print(f"[WARNING] Region detection failed: {str(e)}")
            return []
    
    def _classify_region_type(self, width: int, height: int, area: int, region_gray: np.ndarray) -> str:
        """Classify the type of visual region - all regions are classified as 'table'"""
        # Always return 'table' for all visual regions
        return "table"
    
    def _detect_tables(self, gray: np.ndarray, page_image: Image.Image, page_num: int) -> List[VisualRegion]:
        """Detect table regions using line detection"""
        regions = []
        if not CV2_AVAILABLE:
            return regions
        
        try:
            
            # Detect horizontal lines
            horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
            horizontal_lines = cv2.morphologyEx(gray, cv2.MORPH_OPEN, horizontal_kernel)
            
            # Detect vertical lines
            vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))
            vertical_lines = cv2.morphologyEx(gray, cv2.MORPH_OPEN, vertical_kernel)
            
            # Combine
            table_mask = cv2.addWeighted(horizontal_lines, 0.5, vertical_lines, 0.5, 0.0)
            
            # Find contours of table regions - use RETR_TREE to avoid picking up entire page
            contours, _ = cv2.findContours(table_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            
            page_area = gray.shape[1] * gray.shape[0]  # width * height
            
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                area = w * h
                
                if area < self.min_region_area:
                    continue
                
                # CRITICAL: Reject contours that are too large (likely entire page or large sections)
                # STRICT: Reject if covering more than 50% of page (reduced from 80%)
                region_ratio = area / page_area if page_area > 0 else 0
                if region_ratio > 0.50:  # Reduced from 0.80 to 0.50
                    print(f"[DEBUG] Rejected table contour covering {region_ratio*100:.1f}% of page (max 50% allowed)")
                    continue
                
                bbox = (x, y, x + w, y + h)
                region = self._create_region_from_bbox(bbox, page_image, page_num, "table")
                if region:
                    regions.append(region)
            
            return regions
            
        except Exception as e:
            print(f"[WARNING] Table detection error: {str(e)}")
            return []
    
    def _create_region_from_bbox(self, bbox: Tuple[int, int, int, int], 
                                 page_image: Image.Image, page_num: int, 
                                 region_type: str) -> Optional[VisualRegion]:
        """Create a VisualRegion from bounding box"""
        x0, y0, x1, y1 = bbox
        width = x1 - x0
        height = y1 - y0
        
        # Validate bbox
        if width <= 0 or height <= 0:
            return None
        
        if x0 < 0 or y0 < 0 or x1 > page_image.width or y1 > page_image.height:
            # Clamp to image bounds
            x0 = max(0, x0)
            y0 = max(0, y0)
            x1 = min(page_image.width, x1)
            y1 = min(page_image.height, y1)
            width = x1 - x0
            height = y1 - y0
        
        if width <= 0 or height <= 0:
            return None
        
        # CRITICAL: Reject regions that are too large (likely entire page or large sections)
        # STRICT: Reject if region covers more than 50% of page area (reduced from 80%)
        # This ensures we only get specific visual elements, not large sections with multiple graphs
        page_area = page_image.width * page_image.height
        region_area = width * height
        region_ratio = region_area / page_area if page_area > 0 else 0
        
        if region_ratio > 0.50:  # Reduced from 0.80 to 0.50 (50% max)
            print(f"[DEBUG] Rejected region covering {region_ratio*100:.1f}% of page (too large, max 50% allowed)")
            return None
        
        # Also reject if region is very close to page dimensions (within 10% margin, stricter than before)
        width_ratio = width / page_image.width if page_image.width > 0 else 0
        height_ratio = height / page_image.height if page_image.height > 0 else 0
        
        if width_ratio > 0.90 or height_ratio > 0.90:  # Stricter: reject if >90% in either dimension
            print(f"[DEBUG] Rejected region with dimensions {width}x{height} (width: {width_ratio*100:.1f}%, height: {height_ratio*100:.1f}% of page - too large)")
            return None
        
        # Crop the region
        try:
            cropped = page_image.crop((x0, y0, x1, y1))
            
            # CRITICAL: Enforce minimum size BEFORE checking if blank
            # Lowered minimum size to detect more regions (must be at least 150x100px)
            min_width = 150
            min_height = 100
            if cropped.width < min_width or cropped.height < min_height:
                # Try to expand crop to minimum size while staying within page bounds
                center_x = (x0 + x1) // 2
                center_y = (y0 + y1) // 2
                new_x0 = max(0, center_x - min_width // 2)
                new_y0 = max(0, center_y - min_height // 2)
                new_x1 = min(page_image.width, new_x0 + min_width)
                new_y1 = min(page_image.height, new_y0 + min_height)
                # Adjust if we hit boundaries
                if new_x1 - new_x0 < min_width:
                    new_x0 = max(0, new_x1 - min_width)
                if new_y1 - new_y0 < min_height:
                    new_y0 = max(0, new_y1 - min_height)
                
                # Re-crop with expanded bounds
                cropped = page_image.crop((new_x0, new_y0, new_x1, new_y1))
                width = new_x1 - new_x0
                height = new_y1 - new_y0
                x0, y0, x1, y1 = new_x0, new_y0, new_x1, new_y1
                print(f"[DEBUG] Expanded small region from {x1-x0}x{y1-y0} to {width}x{height}")
            
            # CRITICAL: Reject regions that are still too small after expansion
            # Lowered minimum to allow more regions (must be at least 120x80px)
            if cropped.width < 120 or cropped.height < 80:
                print(f"[DEBUG] Rejected region too small: {cropped.width}x{cropped.height} (minimum: 120x80)")
                return None
            
            # CRITICAL: Check if cropped region is blank/white BEFORE creating VisualRegion
            # This prevents blank regions from being matched to questions
            try:
                import numpy as np
                # Convert to RGB if needed
                check_img = cropped
                if check_img.mode != 'RGB':
                    check_img = check_img.convert('RGB')
                
                # Check if image is mostly blank/white
                img_array = np.array(check_img)
                white_pixels = np.sum(np.all(img_array > 240, axis=2))
                total_pixels = img_array.shape[0] * img_array.shape[1]
                white_ratio = white_pixels / total_pixels if total_pixels > 0 else 0
                variance = np.var(img_array)
                
                # Reject if image is >95% white OR has very low variance (<100)
                if white_ratio > 0.95 or variance < 100:
                    print(f"[DEBUG] Rejected blank/white region at ({x0}, {y0}, {width}x{height}) - white_ratio: {white_ratio:.2f}, variance: {variance:.1f}")
                    return None
            except ImportError:
                # If numpy not available, skip blank check (but log warning)
                print(f"[WARNING] numpy not available, cannot check if region is blank")
            except Exception as e:
                # If check fails, continue (don't reject region on check error)
                print(f"[WARNING] Error checking if region is blank: {str(e)}")
            
            # Calculate confidence based on region characteristics
            # Prefer smaller, more specific regions (inverse relationship with size)
            # Smaller regions that are well-matched get higher confidence
            area = width * height
            page_area = page_image.width * page_image.height
            area_ratio = area / page_area if page_area > 0 else 0
            
            # Confidence calculation: prefer regions that are 10-30% of page (sweet spot)
            # Too small (<5%) or too large (>40%) get lower confidence
            if area_ratio < 0.05:
                confidence = 0.3 + (area_ratio / 0.05) * 0.2  # 0.3-0.5 for very small regions
            elif area_ratio <= 0.30:
                # Sweet spot: 5-30% of page gets high confidence
                confidence = 0.5 + (area_ratio / 0.30) * 0.5  # 0.5-1.0
            else:
                # Larger regions (30-50%) get lower confidence
                confidence = 1.0 - ((area_ratio - 0.30) / 0.20) * 0.4  # 1.0-0.6
            
            region = VisualRegion(
                bbox=(x0, y0, x1, y1),
                page_num=page_num,
                region_type=region_type,
                confidence=confidence,
                image=cropped
            )
            
            return region
            
        except Exception as e:
            print(f"[WARNING] Failed to crop region: {str(e)}")
            return None


class SemanticMatcher:
    """Matches visual regions to questions using semantic similarity"""
    
    def __init__(self):
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load embedding model for semantic matching"""
        try:
            from sentence_transformers import SentenceTransformer
            
            # Use a lightweight model that works well for text-image matching
            model_name = getattr(settings, 'EMBEDDING_MODEL', 'all-MiniLM-L6-v2')
            print(f"[INFO] Loading embedding model: {model_name}")
            self.model = SentenceTransformer(model_name)
            print("[SUCCESS] Embedding model loaded")
            
        except ImportError:
            print("[WARNING] sentence-transformers not installed. Install with: pip install sentence-transformers")
            self.model = None
        except Exception as e:
            print(f"[WARNING] Failed to load embedding model: {str(e)}")
            print("[INFO] Falling back to round-robin matching.")
            self.model = None
    
    def generate_embeddings(self, texts: List[str], batch_size: int = 32) -> Optional[np.ndarray]:
        """Generate embeddings for a list of texts in batches to reduce memory usage"""
        if not self.model:
            return None
        
        try:
            # Force garbage collection before processing
            import gc
            gc.collect()
            
            # Process in batches to avoid memory issues
            if len(texts) > batch_size:
                print(f"[INFO] Processing {len(texts)} texts in batches of {batch_size}...")
                embeddings_list = []
                for i in range(0, len(texts), batch_size):
                    batch = texts[i:i + batch_size]
                    try:
                        batch_embeddings = self.model.encode(
                            batch, 
                            convert_to_numpy=True, 
                            show_progress_bar=False,
                            batch_size=min(batch_size, len(batch)),
                            normalize_embeddings=True  # Normalize to reduce memory
                        )
                        embeddings_list.append(batch_embeddings)
                        print(f"[INFO] Processed batch {i//batch_size + 1}/{(len(texts) + batch_size - 1)//batch_size}")
                        
                        # Force garbage collection after each batch
                        del batch_embeddings
                        gc.collect()
                    except (MemoryError, RuntimeError) as e:
                        print(f"[ERROR] Memory error in batch {i//batch_size + 1}: {str(e)}")
                        # If we have some embeddings, return what we have
                        if embeddings_list:
                            print("[WARNING] Returning partial embeddings due to memory error")
                            return np.vstack(embeddings_list)
                        raise
                
                # Concatenate all batches
                embeddings = np.vstack(embeddings_list)
                del embeddings_list
                gc.collect()
            else:
                embeddings = self.model.encode(
                    texts, 
                    convert_to_numpy=True, 
                    show_progress_bar=False,
                    batch_size=len(texts),
                    normalize_embeddings=True
                )
            return embeddings
        except (MemoryError, RuntimeError, OSError) as e:
            print(f"[ERROR] Failed to generate embeddings (memory/runtime error): {str(e)}")
            import gc
            gc.collect()
            return None
        except Exception as e:
            print(f"[ERROR] Failed to generate embeddings: {str(e)}")
            import traceback
            traceback.print_exc()
            import gc
            gc.collect()
            return None
    
    def match_regions_to_questions(self, regions: List[VisualRegion], 
                                  questions: List[str],
                                  min_confidence: float = 0.25) -> List[Tuple[int, int, float]]:
        """
        Match visual regions to questions using semantic similarity
        Returns list of (question_index, region_index, similarity_score) tuples
        """
        if not regions or not questions:
            print(f"[WARNING] No regions ({len(regions)}) or questions ({len(questions)}) to match")
            return []
        
        if not self.model:
            print("[WARNING] Embedding model not available, no images will be displayed - semantic matching failed")
            return []
        
        try:
<<<<<<< HEAD
            # Process more regions to have a larger database of images to select from
            # Increased limit to 60 regions for better coverage and more matching options
            MAX_SAFE_PROCESSING = 60  # Increased from 30 to 60 for larger image database
=======
            # Optimized: Process fewer regions for faster runtime while maintaining quality
            # Reduced from 60 to 35 for better performance (still provides good coverage)
            MAX_SAFE_PROCESSING = 35  # Optimized for speed: balance between quality and runtime
>>>>>>> parent of 2af5513 (Increase MAX_SAFE_PROCESSING from 35 to 50 regions for better image coverage)
            if len(regions) > MAX_SAFE_PROCESSING:
                print(f"[INFO] Large number of regions ({len(regions)}), processing top {MAX_SAFE_PROCESSING} for comprehensive matching")
                print(f"[INFO] Processing top {MAX_SAFE_PROCESSING} regions (sorted by confidence/quality)")
                # Sort by confidence and take top regions for better quality
                regions = sorted(regions, key=lambda r: r.confidence, reverse=True)[:MAX_SAFE_PROCESSING]
            else:
                print(f"[INFO] Processing all {len(regions)} regions for semantic matching")
            
            # Process all regions up to MAX_REGIONS limit (already limited above)
            # No need for additional fallback - semantic matching can handle up to 50 regions
            
            # Extract text descriptions from regions using OCR
            print(f"[INFO] Extracting text from {len(regions)} regions...")
            region_texts = []
            for idx, region in enumerate(regions):
                text = self._extract_text_from_region(region)
                region_texts.append(text)
                if idx < 3:  # Log first few for debugging
                    print(f"[DEBUG] Region {idx+1} text (first 100 chars): {text[:100]}")
            
            # Generate embeddings with very small batches and aggressive error handling
            print(f"[INFO] Generating embeddings for {len(questions)} questions and {len(region_texts)} regions...")
            try:
                # Process questions first (usually small number)
                # Increased batch size to 16 for faster processing
                question_embeddings = self.generate_embeddings(questions, batch_size=16)
                if question_embeddings is None:
                    raise Exception("Failed to generate question embeddings")
                
                # Process regions with optimized batch size for faster runtime
                # Use larger batches for faster processing (regions now limited to 60)
                if len(region_texts) > 40:
                    # For very large numbers, use medium batches
                    region_batch_size = 10
                elif len(region_texts) > 20:
                    # For larger numbers, use medium batches
                    region_batch_size = 12
                else:
                    # For smaller numbers, use larger batches for speed
                    region_batch_size = 16
                
                print(f"[INFO] Processing {len(region_texts)} regions with batch size {region_batch_size} (estimated {len(region_texts) // region_batch_size + 1} batches)")
                region_embeddings = self.generate_embeddings(region_texts, batch_size=region_batch_size)
                if region_embeddings is None:
                    raise Exception("Failed to generate region embeddings")
                    
            except (MemoryError, RuntimeError, SystemExit, OSError) as e:
                print(f"[ERROR] Memory or runtime error during embedding generation: {str(e)}")
                print("[WARNING] Semantic matching failed due to memory/runtime constraints")
                print("[INFO] No images will be displayed - semantic matching failed")
                import traceback
                traceback.print_exc()
                return []
            except Exception as e:
                print(f"[ERROR] Error during embedding generation: {str(e)}")
                print("[INFO] No images will be displayed - semantic matching failed")
                import traceback
                traceback.print_exc()
                return []
            
            # Calculate cosine similarity
            if not SKLEARN_AVAILABLE:
                print("[WARNING] scikit-learn not available, using manual cosine similarity")
                # Manual cosine similarity calculation
                def cosine_sim(a, b):
                    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
                
                similarity_matrix = np.array([
                    [cosine_sim(q, r) for r in region_embeddings]
                    for q in question_embeddings
                ])
            else:
                similarity_matrix = cosine_similarity(question_embeddings, region_embeddings)
            
            # Find best matches
            matches = []
            used_regions = set()
            
            # Log similarity scores for debugging
            print(f"[INFO] Calculating similarity scores (min_confidence={min_confidence})...")
            max_scores = []
            for q_idx in range(len(questions)):
                max_score = float(np.max(similarity_matrix[q_idx]))
                max_scores.append(max_score)
                if q_idx < 3:  # Log first few
                    print(f"[DEBUG] Question {q_idx+1} max similarity: {max_score:.3f}")
            
            # STRICT: Do not adjust threshold - require high quality matches only
            # If scores don't meet threshold, no images will be displayed (quality over quantity)
            if max_scores and max(max_scores) < min_confidence:
                print(f"[WARNING] Maximum similarity score {max(max_scores):.3f} is below threshold {min_confidence:.3f}")
                print(f"[INFO] No images will be displayed - quality threshold not met (minimum {min_confidence*100:.0f}% similarity required)")
                print(f"[INFO] This ensures only high-quality, well-matched images are shown to users")
                # Log all scores for debugging
                if len(max_scores) <= 10:
                    print(f"[DEBUG] All similarity scores: {[f'{s:.3f}' for s in max_scores]}")
                else:
                    print(f"[DEBUG] Top 10 similarity scores: {[f'{s:.3f}' for s in sorted(max_scores, reverse=True)[:10]]}")
            
            # Sort by similarity score (highest first)
            for q_idx in range(len(questions)):
                best_region_idx = -1
                best_score = min_confidence
                
                for r_idx in range(len(regions)):
                    if r_idx in used_regions:
                        continue
                    
                    score = float(similarity_matrix[q_idx][r_idx])
                    if score > best_score:
                        best_score = score
                        best_region_idx = r_idx
                
                if best_region_idx >= 0:
                    matches.append((q_idx, best_region_idx, best_score))
                    used_regions.add(best_region_idx)
                    print(f"[DEBUG] Matched question {q_idx+1} to region {best_region_idx+1} (score: {best_score:.3f})")
            
            if not matches:
                print(f"[WARNING] No matches found above threshold {min_confidence}")
                print("[INFO] No images will be displayed - semantic matching failed")
                return []
            
            print(f"[INFO] Found {len(matches)} semantic matches")
            return matches
            
        except Exception as e:
            print(f"[ERROR] Semantic matching failed: {str(e)}")
            print("[INFO] No images will be displayed - semantic matching failed")
            import traceback
            traceback.print_exc()
            return []
    
    def _extract_text_from_region(self, region: VisualRegion) -> str:
        """Extract text from a visual region using OCR"""
        if not region.image:
            return f"{region.region_type} visual element"
        
        try:
            import pytesseract
            
            # Convert to RGB if needed
            img = region.image
            if img.mode != 'RGB':
                rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'RGBA':
                    rgb_img.paste(img, mask=img.split()[3])
                else:
                    rgb_img.paste(img)
                img = rgb_img
            
            # Extract text with better config for diagrams/graphs
            text = pytesseract.image_to_string(img, lang='eng', config='--psm 6')
            text = text.strip()
            
            # If OCR returns very little text, try one additional PSM mode for faster processing
            # Reduced from 4 PSM modes to 1 for faster runtime
            if len(text) < 10:
                try:
                    # Try one additional PSM mode (6 is usually best for single blocks)
                    alt_text = pytesseract.image_to_string(img, lang='eng', config='--psm 6')
                    if len(alt_text.strip()) > len(text.strip()):
                        text = alt_text.strip()
                except:
                    pass
                
                # If still no good text, create a minimal descriptive fallback
                if len(text) < 10:
                    text = f"{region.region_type} visual element on page {region.page_num + 1}"
            
            return text
            
        except ImportError:
            # Fallback: create descriptive text
            return f"{region.region_type} on page {region.page_num + 1}"
        except Exception as e:
            # Fallback: create descriptive text
            return f"{region.region_type} on page {region.page_num + 1}"


class VisualRegionPipeline:
    """Main pipeline for detecting and matching visual regions to flashcards"""
    
    def __init__(self):
        self.detector = VisualRegionDetector()
        self.matcher = SemanticMatcher()
    
    def process_document(self, file_path: str, file_type: str, 
                       questions: List[str]) -> List[Tuple[int, VisualRegion, float]]:
        """
        Process a document and match visual regions to questions
        Returns list of (question_index, region, confidence_score) tuples
        COMPREHENSIVE ERROR HANDLING: This method will never raise exceptions, always returns a list
        """
        try:
            print(f"[INFO] Processing document for visual region detection...")
            
            # Detect regions with error handling
            try:
                if file_type == 'application/pdf' or file_path.endswith('.pdf'):
                    regions = self.detector.detect_regions_in_pdf(file_path)
                elif file_type in ['application/vnd.openxmlformats-officedocument.wordprocessingml.document', 
                                  'application/msword'] or file_path.endswith(('.docx', '.doc')):
                    regions = self.detector.detect_regions_in_docx(file_path)
                else:
                    print(f"[WARNING] Unsupported file type for visual region detection: {file_type}")
                    return []
            except Exception as detect_err:
                print(f"[WARNING] Error detecting regions: {type(detect_err).__name__}: {str(detect_err)}")
                return []
            
            if not regions:
                print("[WARNING] No visual regions detected in document")
                return []
            
            print(f"[INFO] Detected {len(regions)} visual regions")
            
<<<<<<< HEAD
            # Process more regions to have a larger database of images to select from
            # Increased limit to 60 regions for better coverage and more matching options
            MAX_SAFE_PROCESSING = 60  # Increased from 30 to 60 for larger image database
=======
            # Optimized: Process fewer regions for faster runtime while maintaining quality
            # Reduced from 60 to 35 for better performance (still provides good coverage)
            MAX_SAFE_PROCESSING = 35  # Optimized for speed: balance between quality and runtime
>>>>>>> parent of 2af5513 (Increase MAX_SAFE_PROCESSING from 35 to 50 regions for better image coverage)
            if len(regions) > MAX_SAFE_PROCESSING:
                print(f"[INFO] Large number of regions ({len(regions)}), processing top {MAX_SAFE_PROCESSING} for comprehensive matching")
                print(f"[INFO] Processing top {MAX_SAFE_PROCESSING} regions (sorted by confidence/quality)")
                # Sort by confidence and take top regions for better quality
                regions = sorted(regions, key=lambda r: r.confidence, reverse=True)[:MAX_SAFE_PROCESSING]
            else:
                print(f"[INFO] Processing all {len(regions)} detected regions for semantic matching")
            
            # Try semantic matching on the (possibly limited) regions
            # Match regions to questions with comprehensive error handling
            try:
                    # Use high confidence threshold for better quality matches
                    # Set to 0.35 (35%) - balanced threshold that ensures quality while allowing good matches
                    # Images below this threshold will not be displayed at all (strict enforcement)
                    matches = self.matcher.match_regions_to_questions(regions, questions, min_confidence=0.35)
            except (MemoryError, RuntimeError, SystemExit, OSError) as mem_err:
                print(f"[ERROR] Memory/runtime error during matching: {type(mem_err).__name__}: {str(mem_err)}")
                print("[INFO] No images will be displayed - semantic matching failed")
                import traceback
                traceback.print_exc()
                matches = []
            except Exception as match_err:
                print(f"[ERROR] Error during semantic matching: {type(match_err).__name__}: {str(match_err)}")
                print("[INFO] No images will be displayed - semantic matching failed")
                import traceback
                traceback.print_exc()
                matches = []
            
            if not matches:
                print("[WARNING] No matches found between questions and regions")
                return []
            
            print(f"[INFO] Matched {len(matches)} questions to visual regions")
            
            # Return matched regions with error handling
            try:
                result = []
                for q_idx, r_idx, score in matches:
                    if r_idx < len(regions):
                        result.append((q_idx, regions[r_idx], score))
                return result
            except Exception as result_err:
                print(f"[WARNING] Error building result list: {type(result_err).__name__}: {str(result_err)}")
                return []
                
        except Exception as outer_err:
            # Ultimate catch-all: never let this method raise an exception
            print(f"[ERROR] Unexpected error in process_document: {type(outer_err).__name__}: {str(outer_err)}")
            import traceback
            traceback.print_exc()
            return []  # Always return empty list, never raise

