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
            self.model = None
    
    def generate_embeddings(self, texts: List[str]) -> Optional[np.ndarray]:
        """Generate embeddings for a list of texts"""
        if not self.model:
            return None
        
        try:
            embeddings = self.model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
            return embeddings
        except Exception as e:
            print(f"[ERROR] Failed to generate embeddings: {str(e)}")
            return None
    
    def match_regions_to_questions(self, regions: List[VisualRegion], 
                                  questions: List[str],
                                  min_confidence: float = 0.3) -> List[Tuple[int, int, float]]:
        """
        Match visual regions to questions using semantic similarity
        Returns list of (question_index, region_index, similarity_score) tuples
        """
        if not self.model or not regions or not questions:
            return []
        
        try:
            # Extract text descriptions from regions using OCR
            region_texts = []
            for region in regions:
                text = self._extract_text_from_region(region)
                region_texts.append(text)
            
            # Generate embeddings
            question_embeddings = self.generate_embeddings(questions)
            region_embeddings = self.generate_embeddings(region_texts)
            
            if question_embeddings is None or region_embeddings is None:
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
            
            return matches
            
        except Exception as e:
            print(f"[ERROR] Semantic matching failed: {str(e)}")
            return []
    
    def _extract_text_from_region(self, region: VisualRegion) -> str:
        """Extract text from a visual region using OCR"""
        if not region.image:
            return ""
        
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
            
            # Extract text
            text = pytesseract.image_to_string(img, lang='eng')
            return text.strip()
            
        except ImportError:
            return f"{region.region_type} on page {region.page_num + 1}"
        except Exception as e:
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
        """
        print(f"[INFO] Processing document for visual region detection...")
        
        # Detect regions
        if file_type == 'application/pdf' or file_path.endswith('.pdf'):
            regions = self.detector.detect_regions_in_pdf(file_path)
        elif file_type in ['application/vnd.openxmlformats-officedocument.wordprocessingml.document', 
                          'application/msword'] or file_path.endswith(('.docx', '.doc')):
            regions = self.detector.detect_regions_in_docx(file_path)
        else:
            print(f"[WARNING] Unsupported file type for visual region detection: {file_type}")
            return []
        
        if not regions:
            print("[WARNING] No visual regions detected in document")
            return []
        
        print(f"[INFO] Detected {len(regions)} visual regions")
        
        # Match regions to questions
        matches = self.matcher.match_regions_to_questions(regions, questions, min_confidence=0.3)
        
        if not matches:
            print("[WARNING] No semantic matches found between questions and regions")
            return []
        
        print(f"[INFO] Matched {len(matches)} questions to visual regions")
        
        # Return matched regions
        result = []
        for q_idx, r_idx, score in matches:
            result.append((q_idx, regions[r_idx], score))
        
        return result

