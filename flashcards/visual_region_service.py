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
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

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
        self.region_type = region_type  # 'graph', 'table', 'diagram', 'formula', 'bullet_cluster'
        self.confidence = confidence
        self.image = image
        self.embedding = None  # Will be populated for semantic matching


class VisualRegionDetector:
    """Detects visual regions in PDF/Word documents"""
    
    def __init__(self):
        self.min_region_area = 5000  # Minimum area in pixels for a valid region
        self.aspect_ratio_range = (0.3, 3.0)  # Valid aspect ratios
    
    def detect_regions_in_pdf(self, file_path: str) -> List[VisualRegion]:
        """Detect visual regions in a PDF document"""
        regions = []
        try:
            import fitz  # PyMuPDF
            
            doc = fitz.open(file_path)
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                
                # Get page as image for processing
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x zoom for better quality
                img_data = pix.tobytes("png")
                page_image = Image.open(io.BytesIO(img_data))
                
                # Detect regions on this page
                page_regions = self._detect_regions_on_page(page, page_image, page_num)
                regions.extend(page_regions)
            
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
                        region_type='diagram',  # Default type
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
            # Fallback: treat entire page as one region
            bbox = (0, 0, page_image.width, page_image.height)
            region = VisualRegion(bbox, page_num, "diagram", 0.5, page_image)
            return [region]
        
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
                        region = self._create_region_from_bbox(bbox, page_image, page_num, "diagram")
                        if region:
                            regions.append(region)
            except:
                pass
            
            # Method 2: Detect using contour analysis (for graphs, tables)
            try:
                # Apply threshold
                _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
                
                # Find contours
                contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                for contour in contours:
                    x, y, w, h = cv2.boundingRect(contour)
                    area = w * h
                    
                    # Filter by size
                    if area < self.min_region_area:
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
        """Classify the type of visual region based on characteristics"""
        if not CV2_AVAILABLE:
            return "diagram"
        
        try:
            
            aspect_ratio = width / height if height > 0 else 1
            
            # Detect horizontal lines (tables)
            horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
            horizontal_lines = cv2.morphologyEx(region_gray, cv2.MORPH_OPEN, horizontal_kernel)
            h_line_count = np.sum(horizontal_lines > 0) / (width * height)
            
            # Detect vertical lines (tables)
            vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))
            vertical_lines = cv2.morphologyEx(region_gray, cv2.MORPH_OPEN, vertical_kernel)
            v_line_count = np.sum(vertical_lines > 0) / (width * height)
            
            # Table detection
            if h_line_count > 0.1 and v_line_count > 0.05:
                return "table"
            
            # Formula detection (usually narrow, tall regions with dense content)
            if aspect_ratio < 0.5 and area > 10000:
                return "formula"
            
            # Bullet cluster (usually vertical list)
            if aspect_ratio < 0.7 and area > 15000:
                return "bullet_cluster"
            
            # Graph (usually square-ish with lines/curves)
            if 0.7 <= aspect_ratio <= 1.5:
                return "graph"
            
            # Default to diagram
            return "diagram"
            
        except:
            return "diagram"
    
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
            
            # Find contours of table regions
            contours, _ = cv2.findContours(table_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                area = w * h
                
                if area > self.min_region_area * 2:  # Tables are usually larger
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
        
        # Crop the region
        try:
            cropped = page_image.crop((x0, y0, x1, y1))
            
            # Calculate confidence based on region characteristics
            area = width * height
            confidence = min(1.0, area / (page_image.width * page_image.height * 0.3))  # Max confidence if >30% of page
            
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
                                  min_confidence: float = 0.3) -> List[Tuple[int, int, float]]:
        """
        Match visual regions to questions using semantic similarity
        Returns list of (question_index, region_index, similarity_score) tuples
        """
        if not regions or not questions:
            print(f"[WARNING] No regions ({len(regions)}) or questions ({len(questions)}) to match")
            return []
        
        if not self.model:
            print("[WARNING] Embedding model not available, using fallback matching")
            # Fallback: match based on region type and round-robin
            return self._fallback_match(regions, questions)
        
        try:
            # AGGRESSIVE: Limit regions to prevent memory issues
            # Railway has limited memory, so we need to be very conservative
            MAX_REGIONS = 20  # Reduced from 50 to 20 to prevent OOM
            if len(regions) > MAX_REGIONS:
                print(f"[WARNING] Too many regions ({len(regions)}), limiting to top {MAX_REGIONS} for memory safety")
                regions = regions[:MAX_REGIONS]
            
            # If still too many regions after limiting, use fallback immediately
            if len(regions) > 30:
                print(f"[WARNING] Too many regions ({len(regions)}) even after limiting, using fallback matching")
                return self._fallback_match(regions, questions)
            
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
                question_embeddings = self.generate_embeddings(questions, batch_size=8)
                if question_embeddings is None:
                    raise Exception("Failed to generate question embeddings")
                
                # Process regions with very small batches to avoid memory issues
                # Use batch size of 4 for regions to minimize memory footprint
                region_embeddings = self.generate_embeddings(region_texts, batch_size=4)
                if region_embeddings is None:
                    raise Exception("Failed to generate region embeddings")
                    
            except (MemoryError, RuntimeError, SystemExit, OSError) as e:
                print(f"[ERROR] Memory or runtime error during embedding generation: {str(e)}")
                print("[WARNING] Falling back to simple matching due to memory constraints")
                return self._fallback_match(regions, questions)
            except Exception as e:
                print(f"[ERROR] Error during embedding generation: {str(e)}")
                print("[WARNING] Falling back to simple matching")
                return self._fallback_match(regions, questions)
            
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
            
            # Lower threshold if all scores are low but above a reasonable minimum
            if max_scores and max(max_scores) < min_confidence and max(max_scores) > 0.15:
                adjusted_threshold = max(0.15, max(max_scores) * 0.8)  # Use 80% of max score
                print(f"[INFO] Adjusting confidence threshold from {min_confidence} to {adjusted_threshold:.3f}")
                min_confidence = adjusted_threshold
            
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
                print(f"[WARNING] No matches found above threshold {min_confidence}, using fallback")
                return self._fallback_match(regions, questions)
            
            print(f"[INFO] Found {len(matches)} semantic matches")
            return matches
            
        except Exception as e:
            print(f"[ERROR] Semantic matching failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return self._fallback_match(regions, questions)
    
    def _fallback_match(self, regions: List[VisualRegion], questions: List[str]) -> List[Tuple[int, int, float]]:
        """Fallback matching when semantic matching fails - uses round-robin with region type hints"""
        print("[INFO] Using fallback matching (round-robin distribution)")
        matches = []
        for q_idx in range(len(questions)):
            r_idx = q_idx % len(regions)
            # Use a default confidence score
            matches.append((q_idx, r_idx, 0.5))
        return matches
    
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
            
            # If OCR returns very little text, create a descriptive fallback
            if len(text) < 10:
                # Create a more descriptive text based on region type
                text = f"{region.region_type} diagram showing {region.region_type} information"
            
            return text
            
        except ImportError:
            # Fallback: create descriptive text
            return f"{region.region_type} diagram on page {region.page_num + 1}"
        except Exception as e:
            # Fallback: create descriptive text
            return f"{region.region_type} diagram on page {region.page_num + 1}"


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
            
            # AGGRESSIVE: Early exit if too many regions to prevent ANY memory issues
            # Use a very conservative limit
            MAX_SAFE_REGIONS = 15  # Reduced from 30 to 15 for maximum safety
            if len(regions) > MAX_SAFE_REGIONS:
                print(f"[WARNING] Too many regions ({len(regions)}) detected. Maximum safe limit is {MAX_SAFE_REGIONS}.")
                print("[INFO] Limiting to top regions and using fallback matching to prevent memory issues")
                regions = regions[:MAX_SAFE_REGIONS]
                # Use fallback matching directly - no semantic matching at all
                matches = self.matcher._fallback_match(regions, questions)
            else:
                # Match regions to questions with comprehensive error handling
                try:
                    matches = self.matcher.match_regions_to_questions(regions, questions, min_confidence=0.3)
                except (MemoryError, RuntimeError, SystemExit, OSError) as mem_err:
                    print(f"[WARNING] Memory/runtime error during matching: {type(mem_err).__name__}: {str(mem_err)}")
                    print("[INFO] Using fallback matching instead")
                    matches = self.matcher._fallback_match(regions, questions)
                except Exception as match_err:
                    print(f"[WARNING] Error during semantic matching: {type(match_err).__name__}: {str(match_err)}")
                    print("[INFO] Using fallback matching instead")
                    matches = self.matcher._fallback_match(regions, questions)
            
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

