"""
File processing utilities to extract text from various file types
"""
import os
import json
import requests
import sys
import io
from pathlib import Path
from django.conf import settings

# Fix Windows console encoding for Unicode characters
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except (AttributeError, ValueError):
        # Python < 3.7 or already configured
        pass

def safe_str(obj):
    """Safely convert object to string, handling Unicode encoding issues"""
    try:
        s = str(obj)
        # Test if it can be encoded safely
        s.encode('utf-8', errors='strict')
        return s
    except (UnicodeEncodeError, UnicodeDecodeError):
        # Fallback: replace problematic characters
        try:
            return str(obj).encode('utf-8', errors='replace').decode('utf-8', errors='replace')
        except:
            return "Unable to encode text (encoding issue)"


def extract_all_images_from_pdf(file_path):
    """
    Extract all pages from a PDF as images
    Returns list of PIL Image objects
    """
    images = []
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(file_path)
        for page_num in range(len(doc)):
            page = doc[page_num]
            # Render page to image (150 DPI for good quality)
            pix = page.get_pixmap(matrix=fitz.Matrix(150/72, 150/72))
            # Convert to PIL Image
            from PIL import Image
            img_data = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_data))
            images.append(img)
        doc.close()
        return images
    except ImportError:
        # Try pdf2image as fallback
        try:
            from pdf2image import convert_from_path
            images = convert_from_path(file_path, dpi=150)
            return images if images else []
        except ImportError:
            pass
    except Exception as e:
        print(f"[WARNING] Failed to extract images from PDF: {str(e)}")
    return images


def extract_first_image_from_pdf(file_path):
    """
    Extract the first page of a PDF as an image (backwards compatibility)
    Returns PIL Image object or None
    """
    images = extract_all_images_from_pdf(file_path)
    return images[0] if images else None


def extract_all_images_from_docx(file_path):
    """
    Extract all images from a Word document
    Returns list of PIL Image objects
    """
    images = []
    try:
        from PIL import Image
        import zipfile
        
        # Open docx as zip
        docx_zip = zipfile.ZipFile(file_path)
        
        # Look for images in the media folder
        image_files = [f for f in docx_zip.namelist() if f.startswith('word/media/') and 
                      any(f.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp'])]
        
        # Sort to ensure consistent order
        image_files.sort()
        
        for image_file in image_files:
            try:
                image_data = docx_zip.read(image_file)
                img = Image.open(io.BytesIO(image_data))
                images.append(img)
            except Exception as e:
                print(f"[WARNING] Failed to extract image {image_file}: {str(e)}")
                continue
        
        docx_zip.close()
    except Exception as e:
        print(f"[WARNING] Failed to extract images from Word document: {str(e)}")
    return images


def extract_first_image_from_docx(file_path):
    """
    Extract the first image from a Word document (backwards compatibility)
    Returns PIL Image object or None
    """
    images = extract_all_images_from_docx(file_path)
    return images[0] if images else None


def match_images_to_flashcards(flashcards_data, image_files_list, text_content):
    """
    Match images to flashcards based on question content and image descriptions using LLM
    First describes each image using vision API, then matches questions to relevant images
    Returns a list of (flashcard_index, image_file_index) tuples, or None if matching fails
    """
    print(f"[DEBUG] match_images_to_flashcards called with {len(flashcards_data)} flashcards and {len(image_files_list) if image_files_list else 0} images")
    
    if not image_files_list or len(image_files_list) == 0:
        print("[WARNING] No images provided for matching")
        return None
    
    if len(image_files_list) == 1:
        # Only one image, assign it to all flashcards
        print("[INFO] Only one image available - assigning to all flashcards")
        return [(i, 0) for i in range(len(flashcards_data))]
    
    try:
        from openai import OpenAI
        
        # Check if Groq API key is configured
        api_key = getattr(settings, 'GROQ_API_KEY', '')
        if not api_key or not isinstance(api_key, str) or api_key.strip() == '':
            print("[INFO] No Groq API key - distributing images in round-robin fashion")
            return [(i, i % len(image_files_list)) for i in range(len(flashcards_data))]
        
        model = getattr(settings, 'GROQ_MODEL', 'llama-3.3-70b-versatile')
        vision_model = getattr(settings, 'GROQ_VISION_MODEL', 'llava-3.1-70b-versatile')
        client = OpenAI(
            api_key=api_key,
            base_url='https://api.groq.com/openai/v1'
        )
        
        # First, get descriptions of each image using vision API
        print(f"[INFO] Analyzing {len(image_files_list)} images to understand their content...")
        image_descriptions = []
        for idx, image_file in enumerate(image_files_list):
            try:
                if hasattr(image_file, 'file') and image_file.file:
                    image_path = image_file.file.path
                    description = understand_image_with_vision(image_path)
                    if description:
                        # Truncate description for prompt
                        desc_short = description[:300] + "..." if len(description) > 300 else description
                        image_descriptions.append(f"Image {idx+1}: {desc_short}")
                    else:
                        image_descriptions.append(f"Image {idx+1}: [Unable to analyze image content]")
                else:
                    image_descriptions.append(f"Image {idx+1}: [Image file not available]")
            except Exception as e:
                print(f"[WARNING] Failed to analyze image {idx+1}: {str(e)}")
                image_descriptions.append(f"Image {idx+1}: [Analysis failed]")
        
        # Create an enhanced prompt to match questions to images with better semantic analysis
        questions_text = "\n".join([f"{i+1}. {card['question']}" for i, card in enumerate(flashcards_data)])
        images_text = "\n".join(image_descriptions)
        
        prompt = f"""You are an expert at matching educational content. Your task is to match flashcard questions to the most relevant images/diagrams.

CRITICAL MATCHING RULES:
1. Match based on SPECIFIC TOPICS and CONCEPTS mentioned in both the question and image description
2. Look for KEYWORDS, TERMINOLOGY, and SUBJECT MATTER that overlap
3. Consider the EDUCATIONAL CONTEXT - what concept is the question testing?
4. An image should DIRECTLY ILLUSTRATE or EXPLAIN the concept asked in the question
5. If multiple images could match, choose the one that is MOST SPECIFIC to the question topic
6. If no image directly matches, choose the CLOSEST related image based on subject matter

We have {len(flashcards_data)} flashcard questions and {len(image_files_list)} images.

Flashcard Questions:
{questions_text}

Image Descriptions (detailed analysis of what each image contains):
{images_text}

ANALYSIS INSTRUCTIONS:
For EACH question, analyze:
- What is the MAIN TOPIC or CONCEPT being asked about?
- What KEYWORDS or TERMINOLOGY appear in the question?
- What SUBJECT AREA does this question belong to?
- Which image description contains the MOST RELEVANT content for answering this question?

Then match each question to the image whose description contains the most relevant content.

IMPORTANT: 
- Each question MUST be matched to exactly ONE image (0-based index)
- You can match multiple questions to the same image if they all relate to that image's content
- Be SPECIFIC - match based on actual content overlap, not just general similarity

Return a JSON array where each element is an object with "question_index" (0-based) and "image_index" (0-based).

Example format:
[
  {{"question_index": 0, "image_index": 2}},
  {{"question_index": 1, "image_index": 0}},
  {{"question_index": 2, "image_index": 2}}
]

Return ONLY the JSON array, no additional text or explanation."""

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are an expert at matching educational content. You analyze question topics and match them to relevant image content. You always return valid JSON arrays."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=2000
        )
        
        content = response.choices[0].message.content.strip()
        
        # Remove markdown code blocks if present
        if content.startswith('```'):
            lines = content.split('\n')
            content = '\n'.join(lines[1:-1]) if lines[-1].startswith('```') else '\n'.join(lines[1:])
        
        # Extract JSON array
        start_idx = content.find('[')
        end_idx = content.rfind(']') + 1
        
        if start_idx == -1 or end_idx <= start_idx:
            print("[WARNING] Could not find JSON array in response. Response content:")
            print(content[:500])  # Print first 500 chars for debugging
            raise ValueError("No JSON array found in API response")
        
        content = content[start_idx:end_idx]
        
        try:
            matches = json.loads(content)
        except json.JSONDecodeError as json_err:
            print(f"[WARNING] Failed to parse JSON from API response: {str(json_err)}")
            print(f"[DEBUG] Content that failed to parse: {content[:500]}")
            raise json_err
        
        # Validate and create mapping
        if not isinstance(matches, list):
            print(f"[WARNING] API response is not a list. Got type: {type(matches)}")
            raise ValueError(f"Expected list, got {type(matches)}")
        
        result = []
        matched_question_indices = set()
        
        for match in matches:
            if isinstance(match, dict) and 'question_index' in match and 'image_index' in match:
                try:
                    q_idx = int(match['question_index'])
                    img_idx = int(match['image_index'])
                    # Validate indices
                    if 0 <= q_idx < len(flashcards_data) and 0 <= img_idx < len(image_files_list):
                        result.append((q_idx, img_idx))
                        matched_question_indices.add(q_idx)
                    else:
                        # Invalid index, use round-robin distribution as fallback
                        print(f"[WARNING] Invalid indices: q_idx={q_idx} (max={len(flashcards_data)-1}), img_idx={img_idx} (max={len(image_files_list)-1})")
                        result.append((q_idx, q_idx % len(image_files_list)))
                        matched_question_indices.add(q_idx)
                except (ValueError, TypeError) as e:
                    print(f"[WARNING] Failed to parse match indices: {match}, error: {str(e)}")
                    continue
        
        # Fill in missing question indices with round-robin distribution
        if len(result) < len(flashcards_data):
            missing_indices = [i for i in range(len(flashcards_data)) if i not in matched_question_indices]
            print(f"[INFO] LLM only matched {len(result)}/{len(flashcards_data)} flashcards. Filling {len(missing_indices)} missing matches with round-robin distribution.")
            for q_idx in missing_indices:
                img_idx = q_idx % len(image_files_list)
                result.append((q_idx, img_idx))
        
        # Sort by question index to maintain order
        result.sort(key=lambda x: x[0])
        
        # Final validation
        if len(result) == len(flashcards_data):
            print(f"[SUCCESS] Successfully matched all {len(flashcards_data)} flashcards to images")
            return result
        else:
            print(f"[WARNING] Result count mismatch: got {len(result)}, expected {len(flashcards_data)}")
            # This shouldn't happen, but fallback to round-robin
            return [(i, i % len(image_files_list)) for i in range(len(flashcards_data))]
        
    except ImportError as e:
        print(f"[ERROR] Required library not installed: {str(e)}")
        print("[INFO] Install with: pip install openai")
        # Fallback: distribute images in round-robin fashion
        return [(i, i % len(image_files_list)) for i in range(len(flashcards_data))]
    except json.JSONDecodeError as e:
        print(f"[ERROR] Failed to parse JSON from API response: {str(e)}")
        print(f"[DEBUG] JSON error position: {getattr(e, 'pos', 'unknown')}")
        # Fallback: distribute images in round-robin fashion
        return [(i, i % len(image_files_list)) for i in range(len(flashcards_data))]
    except ValueError as e:
        print(f"[ERROR] Invalid API response format: {str(e)}")
        # Fallback: distribute images in round-robin fashion
        return [(i, i % len(image_files_list)) for i in range(len(flashcards_data))]
    except Exception as e:
        error_str = str(e).lower()
        error_type = type(e).__name__
        
        print(f"[ERROR] Failed to match images to flashcards - Type: {error_type}, Error: {str(e)}")
        
        # Check for specific API errors
        model_name = getattr(settings, 'GROQ_MODEL', 'llama-3.3-70b-versatile')
        if 'quota' in error_str or 'rate limit' in error_str or '429' in error_str:
            print("[ERROR] Groq API quota/rate limit exceeded")
        elif '401' in error_str or 'unauthorized' in error_str or ('invalid' in error_str and 'key' in error_str):
            print("[ERROR] Groq API key invalid or unauthorized")
        elif 'model' in error_str and ('not found' in error_str or 'invalid' in error_str or 'unavailable' in error_str):
            print(f"[ERROR] Groq model '{model_name}' not available")
        elif 'connection' in error_str or 'timeout' in error_str or 'network' in error_str:
            print("[ERROR] Network/connection error with Groq API")
        else:
            import traceback
            print("[DEBUG] Full traceback:")
            traceback.print_exc()
        
        # Fallback: distribute images in round-robin fashion
        return [(i, i % len(image_files_list)) for i in range(len(flashcards_data))]


def extract_text_from_image_ocr(file_path):
    """
    Extract text from image using OCR (Optical Character Recognition)
    Uses pytesseract/Tesseract for text extraction with improved preprocessing
    """
    try:
        from PIL import Image, ImageEnhance, ImageFilter
        import pytesseract
        
        # Open image
        image = Image.open(file_path)
        original_size = image.size
        
        # Convert to RGB if necessary (some formats like PNG might have RGBA)
        if image.mode != 'RGB':
            # Create a white background and paste the image
            rgb_image = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'RGBA':
                rgb_image.paste(image, mask=image.split()[3])  # Use alpha channel as mask
            else:
                rgb_image.paste(image)
            image = rgb_image
        
        # Improve image quality for better OCR
        # Resize if image is too small (OCR works better on larger images)
        min_size = 300
        if min(image.size) < min_size:
            scale_factor = min_size / min(image.size)
            new_size = (int(image.size[0] * scale_factor), int(image.size[1] * scale_factor))
            image = image.resize(new_size, Image.Resampling.LANCZOS)
        
        # Enhance contrast for better text recognition
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.5)
        
        # Enhance sharpness
        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(1.2)
        
        # Try OCR with different configurations for better accuracy
        ocr_configs = [
            '--psm 6',  # Assume uniform block of text
            '--psm 11',  # Sparse text
            '--psm 12',  # Sparse text with OSD
        ]
        
        all_text = []
        for config in ocr_configs:
            try:
                text = pytesseract.image_to_string(image, lang='eng', config=config)
                if text.strip():
                    all_text.append(text.strip())
            except:
                continue
        
        # Combine results, removing duplicates
        if all_text:
            # Use the longest result (usually most complete)
            combined_text = max(all_text, key=len)
            # Remove duplicate lines
            lines = combined_text.split('\n')
            seen = set()
            unique_lines = []
            for line in lines:
                line_stripped = line.strip()
                if line_stripped and line_stripped not in seen:
                    seen.add(line_stripped)
                    unique_lines.append(line)
            return '\n'.join(unique_lines).strip()
        
        # Fallback to default OCR if configs fail
        text = pytesseract.image_to_string(image, lang='eng')
        return text.strip()
    
    except ImportError:
        print("[WARNING] pytesseract not installed. OCR unavailable. Install with: pip install pytesseract")
        return None
    except Exception as e:
        error_msg = safe_str(e)
        print(f"[WARNING] OCR extraction failed: {error_msg}")
        return None


def auto_crop_image_for_question(image_input, question_text):
    """
    Automatically crop an image to show only the region relevant to a specific question
    Uses AI vision to identify the relevant region and crops it
    Accepts either a file path (str) or a PIL Image object
    Returns cropped PIL Image or None if cropping fails
    """
    try:
        from openai import OpenAI
        import base64
        from PIL import Image
        
        # Check if Groq API key is configured
        api_key = getattr(settings, 'GROQ_API_KEY', '')
        if not api_key or not isinstance(api_key, str) or api_key.strip() == '':
            print("[WARNING] Groq API key not found - auto-cropping unavailable")
            return None
        
        vision_model = getattr(settings, 'GROQ_VISION_MODEL', 'llava-3.1-70b-versatile')
        model = getattr(settings, 'GROQ_MODEL', 'llama-3.3-70b-versatile')
        
        client = OpenAI(
            api_key=api_key,
            base_url='https://api.groq.com/openai/v1'
        )
        
        # Open and prepare image - handle both file path and PIL Image
        if isinstance(image_input, Image.Image):
            image = image_input.copy()
        elif isinstance(image_input, str):
            # Check if it's a valid image file
            try:
                image = Image.open(image_input)
            except Exception as img_err:
                print(f"[WARNING] Auto-crop failed: cannot identify image file '{image_input}': {str(img_err)}")
                return None
        else:
            print(f"[WARNING] Auto-crop failed: invalid image input type: {type(image_input)}")
            return None
        img_width, img_height = image.size
        
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            rgb_image = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'RGBA':
                rgb_image.paste(image, mask=image.split()[3])
            else:
                rgb_image.paste(image)
            image = rgb_image
        
        # Save image to bytes and encode to base64
        import io
        image_buffer = io.BytesIO()
        image.save(image_buffer, format='PNG')
        image_bytes = image_buffer.getvalue()
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        
        # Create prompt to identify relevant region
        prompt = f"""Analyze this image and identify the SPECIFIC REGION that is most relevant to answering this question:

QUESTION: {question_text}

Your task:
1. Identify which part/region of the image directly relates to this question
2. Describe the location of this region (e.g., "top-left", "center", "bottom-right", "left side", etc.)
3. Estimate the approximate coordinates as percentages:
   - x_percent: horizontal position (0-100, where 0 is left edge, 100 is right edge)
   - y_percent: vertical position (0-100, where 0 is top edge, 100 is bottom edge)
   - width_percent: width of relevant region (0-100)
   - height_percent: height of relevant region (0-100)

If the ENTIRE image is relevant, return: x_percent=0, y_percent=0, width_percent=100, height_percent=100

Return ONLY a JSON object with these exact fields:
{{"x_percent": <number>, "y_percent": <number>, "width_percent": <number>, "height_percent": <number>, "reason": "<brief explanation>"}}

Example: {{"x_percent": 10, "y_percent": 20, "width_percent": 60, "height_percent": 50, "reason": "The relevant graph is in the top-left portion"}}"""
        
        try:
            # For now, skip auto-crop with Groq vision API due to format compatibility issues
            # The visual regions are already cropped from the page, so we can use them directly
            # TODO: Implement proper Groq vision API format when vision models support it
            print("[INFO] Auto-crop with Groq vision API temporarily disabled - using visual region directly")
            return None  # Return None to use the visual region image directly
            
            content = response.choices[0].message.content.strip()
            
            # Extract JSON
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1
            
            if start_idx != -1 and end_idx > start_idx:
                content = content[start_idx:end_idx]
                crop_data = json.loads(content)
                
                # Convert percentages to pixel coordinates
                x = int((crop_data.get('x_percent', 0) / 100) * img_width)
                y = int((crop_data.get('y_percent', 0) / 100) * img_height)
                width = int((crop_data.get('width_percent', 100) / 100) * img_width)
                height = int((crop_data.get('height_percent', 100) / 100) * img_height)
                
                # Ensure coordinates are within bounds
                x = max(0, min(x, img_width))
                y = max(0, min(y, img_height))
                width = min(width, img_width - x)
                height = min(height, img_height - y)
                
                # Add some padding (10% on each side) to include context
                padding_x = int(width * 0.1)
                padding_y = int(height * 0.1)
                x = max(0, x - padding_x)
                y = max(0, y - padding_y)
                width = min(img_width - x, width + (2 * padding_x))
                height = min(img_height - y, height + (2 * padding_y))
                
                if width > 0 and height > 0:
                    # STRICT: Only crop if the region is significantly smaller than the full image
                    # Require at least 40% reduction (region must be <60% of original)
                    # This ensures we get specific visual elements, not large sections
                    crop_area = width * height
                    full_area = img_width * img_height
                    crop_ratio = crop_area / full_area if full_area > 0 else 1.0
                    
                    if crop_ratio < 0.60:  # Stricter: only crop if region is less than 60% of image (was 80%)
                        # Crop the image
                        cropped = image.crop((x, y, x + width, y + height))
                        print(f"[INFO] Auto-cropped image: region at ({x}, {y}) size {width}x{height} ({int(crop_ratio*100)}% of original), reason: {crop_data.get('reason', 'N/A')}")
                        return cropped
                    else:
                        print(f"[WARNING] Identified region is too large ({int(crop_ratio*100)}% of image, max 60% allowed) - rejecting crop")
                        return None  # Return None to indicate region is too large, don't use it
                else:
                    print("[WARNING] Invalid crop dimensions, skipping crop")
                    return None
            else:
                print("[WARNING] Could not parse crop coordinates, skipping crop")
                return None
                
        except Exception as api_error:
            print(f"[WARNING] Auto-crop API call failed: {str(api_error)}")
            return None  # Return None to indicate cropping failed, use full image
    
    except ImportError:
        print("[WARNING] OpenAI library not installed. Auto-cropping unavailable.")
        return None
    except Exception as e:
        print(f"[WARNING] Auto-crop failed: {str(e)}")
        return None


def understand_image_with_vision(file_path):
    """
    Understand images and diagrams using vision models (Groq Vision API)
    Returns a description of the image including diagram analysis
    """
    try:
        from openai import OpenAI
        import base64
        from PIL import Image
        
        # Check if Groq API key is configured
        api_key = getattr(settings, 'GROQ_API_KEY', '')
        if not api_key or not isinstance(api_key, str) or api_key.strip() == '':
            print("[WARNING] Groq API key not found - vision analysis unavailable")
            return None
        
        # Groq vision model (supports image input)
        vision_model = getattr(settings, 'GROQ_VISION_MODEL', 'llava-3.1-70b-versatile')
        print(f"[INFO] Using Groq Vision model: {vision_model} for image analysis")
        
        # Create Groq client (OpenAI-compatible API)
        client = OpenAI(
            api_key=api_key,
            base_url='https://api.groq.com/openai/v1'
        )
        
        # Open and prepare image
        image = Image.open(file_path)
        
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            rgb_image = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'RGBA':
                rgb_image.paste(image, mask=image.split()[3])
            else:
                rgb_image.paste(image)
            image = rgb_image
        
        # Save image to bytes and encode to base64
        import io
        image_buffer = io.BytesIO()
        image.save(image_buffer, format='PNG')
        image_bytes = image_buffer.getvalue()
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        
        # Create enhanced prompt for diagram understanding with focus on educational content matching
        prompt = """Analyze this image in EXTREME detail for educational content matching. This description will be used to match images to flashcard questions.

CRITICAL: Focus on identifying the SPECIFIC TOPICS, CONCEPTS, and SUBJECT MATTER shown in this image.

If this image contains a diagram, chart, graph, flowchart, or any visual representation:

1. **Text Content**: List ALL text labels, annotations, captions, titles, axis labels, legends, and any readable text. Include exact wording when possible.

2. **Subject Matter**: Identify the SPECIFIC academic subject, topic, or field (e.g., "microeconomics", "biology", "chemistry", "mathematics", "physics", "history", etc.)

3. **Key Concepts**: List the MAIN CONCEPTS, THEORIES, or PRINCIPLES illustrated (e.g., "supply and demand", "photosynthesis", "chemical equilibrium", "derivatives", etc.)

4. **Visual Elements**: Describe:
   - Chart/graph types (bar chart, line graph, scatter plot, pie chart, etc.)
   - Axes labels and what they represent
   - Data points, trends, or patterns shown
   - Arrows, lines, shapes, symbols and their meanings
   - Color coding or visual distinctions
   - Spatial relationships and layout

5. **Educational Context**: 
   - What specific question or topic would this image help answer?
   - What educational concepts does it demonstrate?
   - What would a student need to understand to interpret this image?

6. **Keywords for Matching**: Provide 5-10 KEYWORDS or PHRASES that would help match this image to relevant questions (e.g., "tax on buyer", "price floor", "demand curve shift", "consumer surplus", etc.)

Be EXTREMELY SPECIFIC and DETAILED. This description will be used to automatically match images to flashcard questions, so include all relevant educational terminology and concepts."""

        # Generate description using Groq vision model
        # Note: Groq's API format requires the content to be a string with the image as base64
        # Some models may not support the array format, so we'll use a text-only approach
        try:
            # For Groq, we need to check if the model supports vision
            # If it does, use the proper format; otherwise, describe the image differently
            response = client.chat.completions.create(
                model=vision_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at analyzing diagrams, charts, and visual representations. Provide detailed, comprehensive descriptions that help understand the visual content."
                    },
                    {
                        "role": "user",
                        "content": prompt  # Groq may not support image_url format, use text-only for now
                    }
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            description = response.choices[0].message.content.strip()
            return description
        except Exception as api_error:
            error_str = str(api_error).lower()
            error_type = type(api_error).__name__
            
            print(f"[ERROR] Groq Vision API call failed - Type: {error_type}, Error: {str(api_error)}")
            
            # Check for specific error types
            if 'quota' in error_str or 'rate limit' in error_str or '429' in error_str:
                print(f"[ERROR] Groq quota/rate limit exceeded: {str(api_error)}")
            elif '401' in error_str or 'unauthorized' in error_str or ('invalid' in error_str and 'key' in error_str):
                print(f"[ERROR] Groq API key invalid or unauthorized: {str(api_error)}")
            elif 'model' in error_str and ('not found' in error_str or 'invalid' in error_str or 'unavailable' in error_str):
                print(f"[ERROR] Groq vision model '{vision_model}' not available: {str(api_error)}")
                print("[INFO] Try a different vision model or check Groq documentation for available models.")
            else:
                print(f"[ERROR] Groq vision analysis error (unexpected): {str(api_error)}")
            
            return None
    
    except ImportError:
        print("[WARNING] OpenAI library not installed. Vision analysis unavailable. Install with: pip install openai")
        return None
    except Exception as e:
        error_msg = safe_str(e)
        print(f"[WARNING] Vision analysis failed: {error_msg}")
        return None


def extract_first_image_from_pdf(file_path):
    """
    Extract the first page of a PDF as an image
    Returns PIL Image object or None
    """
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(file_path)
        if len(doc) > 0:
            # Get first page
            page = doc[0]
            # Render page to image (150 DPI for good quality)
            pix = page.get_pixmap(matrix=fitz.Matrix(150/72, 150/72))
            # Convert to PIL Image
            from PIL import Image
            img_data = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_data))
            doc.close()
            return img
    except ImportError:
        # Try pdf2image as fallback
        try:
            from pdf2image import convert_from_path
            images = convert_from_path(file_path, first_page=1, last_page=1, dpi=150)
            if images:
                return images[0]
        except ImportError:
            pass
    except Exception as e:
        print(f"[WARNING] Failed to extract image from PDF: {str(e)}")
    return None


def extract_first_image_from_docx(file_path):
    """
    Extract the first image from a Word document
    Returns PIL Image object or None
    """
    try:
        from docx import Document
        from PIL import Image
        import io
        import zipfile
        
        # Open docx as zip
        docx_zip = zipfile.ZipFile(file_path)
        
        # Look for images in the media folder
        image_files = [f for f in docx_zip.namelist() if f.startswith('word/media/') and 
                      any(f.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp'])]
        
        if image_files:
            # Get first image
            image_data = docx_zip.read(image_files[0])
            img = Image.open(io.BytesIO(image_data))
            docx_zip.close()
            return img
        docx_zip.close()
    except Exception as e:
        print(f"[WARNING] Failed to extract image from Word document: {str(e)}")
    return None


def extract_text_from_file(file_path, file_type):
    """
    Extract text content from various file types including images
    Returns the extracted text as a string
    """
    import io
    text = ""
    
    try:
        if file_type == 'text/plain' or file_path.endswith('.txt'):
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
        
        elif file_type == 'application/pdf' or file_path.endswith('.pdf'):
            try:
                import PyPDF2
                with open(file_path, 'rb') as f:
                    pdf_reader = PyPDF2.PdfReader(f)
                    text = ""
                    for page in pdf_reader.pages:
                        text += page.extract_text() + "\n"
            except ImportError:
                text = "PDF processing requires PyPDF2. Please install it."
        
        elif file_type in ['application/vnd.openxmlformats-officedocument.wordprocessingml.document', 
                          'application/msword'] or file_path.endswith(('.docx', '.doc')):
            try:
                from docx import Document
                doc = Document(file_path)
                text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            except ImportError:
                text = "Word document processing requires python-docx. Please install it."
        
        elif file_type in ['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                          'application/vnd.ms-excel'] or file_path.endswith(('.xlsx', '.xls')):
            try:
                import openpyxl
                workbook = openpyxl.load_workbook(file_path)
                text = ""
                for sheet in workbook.worksheets:
                    for row in sheet.iter_rows(values_only=True):
                        text += " ".join([str(cell) if cell else "" for cell in row]) + "\n"
            except ImportError:
                text = "Excel processing requires openpyxl. Please install it."
        
        # Image file types - use OCR and Vision API
        elif file_type in ['image/png', 'image/jpeg', 'image/jpg', 'image/gif', 'image/bmp', 'image/webp'] or \
             file_path.endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp')):
            print("[INFO] Processing image file with OCR and vision analysis...")
            
            # Combine OCR text extraction and vision understanding
            ocr_text = extract_text_from_image_ocr(file_path)
            vision_description = understand_image_with_vision(file_path)
            
            # Combine both sources of information
            parts = []
            if vision_description:
                parts.append("=== Visual Diagram Analysis ===\n" + vision_description)
            if ocr_text and len(ocr_text.strip()) > 0:
                parts.append("\n=== Extracted Text from Image ===\n" + ocr_text)
            
            if parts:
                text = "\n\n".join(parts)
            else:
                # If both fail, provide helpful message
                text = "Unable to extract text or analyze image. Please ensure:\n" + \
                       "1. pytesseract is installed (pip install pytesseract)\n" + \
                       "2. Tesseract OCR is installed on your system\n" + \
                       "3. Gemini API key is configured for vision analysis (optional but recommended)"
        
        else:
            # Try to read as plain text
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    text = f.read()
            except:
                text = f"Unsupported file type: {file_type}"
    
    except Exception as e:
        # Safely handle encoding errors
        error_msg = safe_str(e)
        text = f"Error processing file: {error_msg}"
    
    return text


def calculate_flashcard_count(text):
    """
    Calculate the optimal number of flashcards based on content length
    Uses a smart algorithm based on word count, sentence count, and content density
    REDUCED counts for more focused learning
    
    Algorithm:
    - Short files (< 200 words): 3-5 flashcards
    - Medium files (200-1000 words): 5-10 flashcards  
    - Long files (1000-3000 words): 10-20 flashcards
    - Very long files (3000+ words): 20-30 flashcards (max)
    """
    if not text or len(text.strip()) == 0:
        return 3  # Minimum for very short content
    
    # Calculate various metrics
    word_count = len(text.split())
    sentences = text.replace('!', '.').replace('?', '.').split('.')
    sentence_count = len([s for s in sentences if len(s.strip()) > 20])
    
    # Primary calculation based on word count with REDUCED scaling
    if word_count < 100:
        # Very short: 3-5 flashcards
        base_count = max(3, min(5, word_count // 25))
    elif word_count < 200:
        # Short: 4-6 flashcards
        base_count = 4 + (word_count - 100) // 50
    elif word_count < 500:
        # Small: 5-8 flashcards
        base_count = 5 + (word_count - 200) // 100
    elif word_count < 1000:
        # Medium: 8-12 flashcards
        base_count = 8 + (word_count - 500) // 125
    elif word_count < 2000:
        # Large: 12-18 flashcards
        base_count = 12 + (word_count - 1000) // 167
    elif word_count < 3000:
        # Very large: 18-25 flashcards
        base_count = 18 + (word_count - 2000) // 200
    elif word_count < 5000:
        # Extra large: 25-30 flashcards
        base_count = 25 + (word_count - 3000) // 400
    else:
        # Huge: 30 flashcards max (reduced from 100)
        base_count = 30
    
    # Adjust based on sentence count (more sentences = more concepts)
    if sentence_count > 0:
        # Use sentence count as a secondary metric (reduced)
        sentence_based = min(30, max(3, sentence_count // 4))  # Reduced from // 2
        # Average the two approaches for better accuracy
        base_count = int((base_count + sentence_based) / 2)
    
    # Ensure reasonable bounds (3-30 flashcards, reduced from 5-100)
    final_count = max(3, min(30, int(base_count)))
    
    return final_count


def summarize_text(text, max_sentences=10):
    """
    Summarize text by extracting key sentences
    This is a simple extractive summarization approach
    For production, consider using NLP libraries like NLTK or spaCy
    """
    if not text or len(text.strip()) == 0:
        return "No content to summarize."
    
    # Split into sentences (simple approach)
    sentences = text.replace('!', '.').replace('?', '.').split('.')
    sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
    
    if len(sentences) <= max_sentences:
        return '. '.join(sentences) + '.'
    
    # Take first, middle, and last sentences for diversity
    step = len(sentences) // max_sentences
    selected = []
    for i in range(0, len(sentences), step):
        if len(selected) < max_sentences:
            selected.append(sentences[i])
    
    return '. '.join(selected) + '.'


def generate_flashcards_with_ollama(text, num_flashcards=10):
    """
    Generate flashcards using Ollama (FREE, local LLM)
    """
    try:
        base_url = getattr(settings, 'OLLAMA_BASE_URL', 'http://localhost:11434')
        model = getattr(settings, 'OLLAMA_MODEL', 'mistral')
        
        # Truncate text if too long
        max_chars = 6000  # Ollama models can handle less than GPT
        if len(text) > max_chars:
            text = text[:max_chars] + "..."
        
        prompt = f"""Generate {num_flashcards} high-quality educational flashcards from the following text. 
Each flashcard should have a clear, concise question and a comprehensive answer.

Text content:
{text}

Generate exactly {num_flashcards} flashcards in JSON format as a list of objects, each with "question" and "answer" fields.
Example format:
[
  {{"question": "What is...?", "answer": "..."}},
  {{"question": "Explain...", "answer": "..."}}
]

Return ONLY the JSON array, no additional text or explanation."""

        # Call Ollama API
        response = requests.post(
            f"{base_url}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "num_predict": 2000
                }
            },
            timeout=60  # 60 second timeout
        )
        
        if response.status_code != 200:
            return None
        
        result = response.json()
        content = result.get('response', '').strip()
        
        # Remove markdown code blocks if present
        if content.startswith('```'):
            lines = content.split('\n')
            content = '\n'.join(lines[1:-1]) if lines[-1].startswith('```') else '\n'.join(lines[1:])
        
        # Try to extract JSON from response
        # Sometimes Ollama adds extra text, so find JSON array
        start_idx = content.find('[')
        end_idx = content.rfind(']') + 1
        
        if start_idx != -1 and end_idx > start_idx:
            content = content[start_idx:end_idx]
        
        # Parse JSON
        flashcards = json.loads(content)
        
        # Validate and format
        if isinstance(flashcards, list):
            formatted_flashcards = []
            for card in flashcards:
                if isinstance(card, dict) and 'question' in card and 'answer' in card:
                    formatted_flashcards.append({
                        'question': str(card['question']).strip(),
                        'answer': str(card['answer']).strip()
                    })
            return formatted_flashcards if formatted_flashcards else None
        
        return None
        
    except requests.exceptions.RequestException:
        # Ollama not running or connection failed
        return None
    except json.JSONDecodeError:
        # Failed to parse JSON, fall back to rule-based
        return None
    except Exception as e:
        # Any other error, fall back to rule-based
        print(f"Ollama generation error: {str(e)}")
        return None


def generate_flashcards_with_groq(text, num_flashcards=10):
    """
    Generate flashcards using Groq (FREE, cloud-based, very fast!)
    Works on all cloud platforms - perfect for deployment!
    """
    try:
        from openai import OpenAI
        
        # Check if API key is configured (validate it's not empty/whitespace)
        api_key = getattr(settings, 'GROQ_API_KEY', '')
        if not api_key or not isinstance(api_key, str) or api_key.strip() == '':
            print("[WARNING] Groq API key not found or empty - falling back to rule-based generation")
            print(f"[DEBUG] API key type: {type(api_key)}, length: {len(str(api_key)) if api_key else 0}")
            return None
        
        model = getattr(settings, 'GROQ_MODEL', 'llama-3.3-70b-versatile')
        print(f"[INFO] Using Groq LLM: {model} for flashcard generation")
        print(f"[DEBUG] API key present: {bool(api_key)}, starts with 'gsk_': {api_key.startswith('gsk_') if api_key else False}")
        
        # Create Groq client (OpenAI-compatible API)
        client = OpenAI(
            api_key=api_key,
            base_url='https://api.groq.com/openai/v1'
        )
        
        # Truncate text if too long
        max_chars = 8000  # Leave room for prompt
        if len(text) > max_chars:
            text = text[:max_chars] + "..."

        prompt = f"""You are creating {num_flashcards} educational flashcards with CONCISE answers containing key points.

CRITICAL REQUIREMENT - YOU MUST FOLLOW THIS:
**ALL ANSWERS MUST ONLY USE INFORMATION FROM THE TEXT PROVIDED BELOW. DO NOT use any external knowledge, general knowledge, or information from your training data. If information is not in the text, do not include it in the answer.**

STRICT REQUIREMENTS - FOLLOW THESE EXACTLY:
1. Each answer MUST be CONCISE (up to 150 words maximum) - summarize key points clearly
2. Questions MUST test understanding - use "How", "Why", "Explain", "Compare", "What are the key differences"
3. NEVER create simple "What is X?" questions with one-word answers
4. Focus on: key processes, main differences, essential relationships, critical applications
5. Answers should be brief but informative - cover main concepts without excessive detail
6. **ONLY use information that is explicitly stated or clearly implied in the text below**
7. **DO NOT add information from your general knowledge - stick strictly to the provided text**

Text content from uploaded document:
{text}

Generate exactly {num_flashcards} flashcards in JSON format with "question" and "answer" fields.

REQUIRED FORMAT - Answers must be CONCISE and summarized:
- Question types: "How does...", "Explain why...", "What are the key differences...", "Compare...", "What are the main steps..."
- Answers: Concise summaries with key points (up to 150 words, NOT lengthy explanations)
- **Answers must ONLY contain information from the text above - no external knowledge**

EXAMPLES OF WHAT TO CREATE (based on text content):
{{"question": "How does [process from text] work?", "answer": "[Answer using ONLY information from the text above]"}}

{{"question": "What are the key differences between [concepts from text]?", "answer": "[Answer using ONLY information from the text above]"}}

EXAMPLES OF WHAT NOT TO CREATE (REJECT THESE):
- {{"question": "What is DNA?", "answer": "Genetic material."}}  ❌ TOO SIMPLE
- {{"question": "Define respiration.", "answer": "A process."}}  ❌ TOO SIMPLE  
- Answers using information NOT in the text  ❌ WRONG - ONLY use text content
- Long answers over 150 words  ❌ TOO LENGTHY

Generate ONLY concise flashcards with summarized answers (up to 150 words) using ONLY information from the text provided. Return ONLY the JSON array."""

        try:
            response = client.chat.completions.create(
                model=model,
            messages=[
                {"role": "system", "content": "You are an expert educational content creator. You create CONCISE flashcards with summarized answers (up to 150 words) containing key points. CRITICAL: You MUST ONLY use information from the provided text document - NEVER use external knowledge or general information. You NEVER create simple vocabulary tests or one-word answers. Answers should be concise but informative, based ONLY on the provided text. You always return valid JSON."},
                {"role": "user", "content": prompt}
            ],
                temperature=0.9,  # Higher temperature for more creative, comprehensive questions
                max_tokens=4000  # Increased further to allow for very detailed answers
            )
        except Exception as api_error:
            # Re-raise to be caught by outer exception handler with better context
            raise api_error
        
        # Extract JSON from response
        content = response.choices[0].message.content.strip()
        
        # Remove markdown code blocks if present
        if content.startswith('```'):
            lines = content.split('\n')
            content = '\n'.join(lines[1:-1]) if lines[-1].startswith('```') else '\n'.join(lines[1:])
        
        # Try to extract JSON from response
        start_idx = content.find('[')
        end_idx = content.rfind(']') + 1
        
        if start_idx != -1 and end_idx > start_idx:
            content = content[start_idx:end_idx]
        
        # Try to fix common JSON issues (unterminated strings, incomplete arrays)
        # If JSON parsing fails, try to extract valid flashcards from partial JSON
        flashcards = None
        try:
            flashcards = json.loads(content)
        except json.JSONDecodeError as json_error:
            print(f"[WARNING] Initial JSON parse failed: {str(json_error)}")
            print("[INFO] Attempting to fix malformed JSON...")
            
            # Try multiple strategies to recover valid flashcards from malformed JSON
            try:
                import re
                
                # Strategy 1: Find complete flashcard objects using regex (handles escaped quotes)
                pattern = r'\{"question"\s*:\s*"((?:[^"\\]|\\.)*)"\s*,\s*"answer"\s*:\s*"((?:[^"\\]|\\.)*)"\s*\}'
                matches = re.findall(pattern, content)
                
                if matches and len(matches) > 0:
                    flashcards = []
                    for question, answer in matches:
                        # Properly unescape JSON strings
                        try:
                            # Use json.loads to properly unescape
                            question = json.loads(f'"{question}"')
                            answer = json.loads(f'"{answer}"')
                            flashcards.append({'question': question, 'answer': answer})
                        except:
                            # Fallback: manual unescape
                            question = question.replace('\\"', '"').replace('\\n', '\n').replace('\\\\', '\\')
                            answer = answer.replace('\\"', '"').replace('\\n', '\n').replace('\\\\', '\\')
                            flashcards.append({'question': question, 'answer': answer})
                    print(f"[INFO] Extracted {len(flashcards)} flashcards using regex pattern")
                
                # Strategy 2: If regex didn't work, try finding complete objects by balanced braces
                if not flashcards or len(flashcards) == 0:
                    # Find all complete JSON objects by tracking brace balance
                    objects = []
                    brace_count = 0
                    obj_start = -1
                    in_string = False
                    escape_next = False
                    
                    for i, char in enumerate(content):
                        if escape_next:
                            escape_next = False
                            continue
                        if char == '\\':
                            escape_next = True
                            continue
                        if char == '"' and not escape_next:
                            in_string = not in_string
                            continue
                        if in_string:
                            continue
                        if char == '{':
                            if brace_count == 0:
                                obj_start = i
                            brace_count += 1
                        elif char == '}':
                            brace_count -= 1
                            if brace_count == 0 and obj_start >= 0:
                                # Found a complete object
                                obj_str = content[obj_start:i+1]
                                try:
                                    obj = json.loads(obj_str)
                                    if isinstance(obj, dict) and 'question' in obj and 'answer' in obj:
                                        objects.append(obj)
                                except:
                                    pass
                                obj_start = -1
                    
                    if objects:
                        flashcards = objects
                        print(f"[INFO] Extracted {len(flashcards)} flashcards using brace balancing")
                    
                    # Strategy 3: Try parsing up to the error position
                    if not flashcards or len(flashcards) == 0:
                        error_pos = json_error.pos if hasattr(json_error, 'pos') else len(content)
                        # Try to find the last complete object before the error
                        for pos in range(error_pos, max(0, error_pos - 5000), -100):
                            try:
                                partial = content[:pos]
                                # Try to close any open structures
                                if partial.count('[') > partial.count(']'):
                                    partial += ']'
                                if partial.count('{') > partial.count('}'):
                                    partial += '}'
                                test_flashcards = json.loads(partial)
                                if isinstance(test_flashcards, list) and len(test_flashcards) > 0:
                                    flashcards = test_flashcards
                                    print(f"[INFO] Parsed partial JSON (up to position {pos})")
                                    break
                            except:
                                continue
            except Exception as fix_error:
                print(f"[WARNING] JSON fix attempt failed: {str(fix_error)}")
            
            # If still no flashcards, raise the original error
            if not flashcards:
                raise json_error
        
        # Validate and format - filter out simple/short flashcards
        if isinstance(flashcards, list):
            formatted_flashcards = []
            for card in flashcards:
                if isinstance(card, dict) and 'question' in card and 'answer' in card:
                    question = str(card['question']).strip()
                    answer = str(card['answer']).strip()
                    
                    # Filter out simple flashcards
                    # Skip if answer is too short (less than 20 characters)
                    if len(answer) < 20:
                        print(f"[FILTER] Skipping flashcard - answer too short: {question[:50]}...")
                        continue
                    
                    # Skip if answer has too few words (need at least 5 words for meaningful answer)
                    answer_words = answer.split()
                    if len(answer_words) < 5:
                        print(f"[FILTER] Skipping flashcard - answer too simple ({len(answer_words)} words): {question[:50]}...")
                        continue
                    
                    # Skip if answer is too long (over 150 words - should be concise!)
                    if len(answer_words) > 150:
                        print(f"[FILTER] Skipping flashcard - answer too lengthy ({len(answer_words)} words, max 150): {question[:50]}...")
                        continue
                    
                    # Skip if question is too simple (just "What is X?" or "Define X") with very short answer
                    question_lower = question.lower()
                    if (question_lower.startswith('what is ') and len(question.split()) < 4) or \
                       (question_lower.startswith('define ') and len(question.split()) < 3):
                        # Check if answer is also too short/simple
                        if len(answer_words) < 8:
                            print(f"[FILTER] Skipping flashcard - too simple question/answer: {question[:50]}...")
                            continue
                    
                    formatted_flashcards.append({
                        'question': question,
                        'answer': answer
                    })
            
            # If we filtered out too many, warn but still return what we have
            if len(formatted_flashcards) < num_flashcards * 0.5:  # Less than 50% passed
                print(f"[WARNING] Only {len(formatted_flashcards)}/{num_flashcards} flashcards passed quality filter")
                if len(formatted_flashcards) == 0:
                    return None  # None passed, fall back to rule-based
            
            print(f"[SUCCESS] {len(formatted_flashcards)} comprehensive flashcards generated after filtering")
            return formatted_flashcards if formatted_flashcards else None
        
        return None
        
    except ImportError:
        # OpenAI library not installed
        print("[ERROR] OpenAI library not installed for Groq. Install with: pip install openai")
        return None
    except json.JSONDecodeError as e:
        # Failed to parse JSON, fall back to rule-based
        print(f"[ERROR] Groq JSON decode error: {str(e)}. Response may be malformed.")
        return None
    except Exception as e:
        # Check for specific Groq API errors
        error_str = str(e).lower()
        error_type = type(e).__name__
        
        print(f"[ERROR] Groq API call failed - Type: {error_type}, Error: {str(e)}")
        
        # Quota/rate limit errors
        if 'quota' in error_str or 'rate limit' in error_str or '429' in error_str:
            print(f"[ERROR] Groq quota/rate limit exceeded: {str(e)}")
            print("[INFO] You may have run out of free tier tokens. Check your Groq dashboard.")
        # Authentication errors
        elif '401' in error_str or 'unauthorized' in error_str or ('invalid' in error_str and 'key' in error_str):
            print(f"[ERROR] Groq API key invalid or unauthorized: {str(e)}")
            print("[INFO] Check your GROQ_API_KEY environment variable.")
            print(f"[DEBUG] API key starts with 'gsk_': {api_key.startswith('gsk_') if api_key else 'N/A'}")
        # Model errors
        elif 'model' in error_str and ('not found' in error_str or 'invalid' in error_str or 'unavailable' in error_str):
            print(f"[ERROR] Groq model '{model}' not available: {str(e)}")
            print("[INFO] The specified model may not be available. Check GROQ_MODEL setting.")
        # Network errors
        elif 'connection' in error_str or 'timeout' in error_str or 'network' in error_str:
            print(f"[ERROR] Groq network/connection error: {str(e)}")
            print("[INFO] Check your internet connection or Groq API status.")
        # Generic error
        else:
            print(f"[ERROR] Groq generation error (unexpected): {str(e)}")
            print(f"[DEBUG] Full error details: {repr(e)}")
        
        print("[INFO] Falling back to rule-based flashcard generation.")
        return None


def generate_flashcards_with_gemini(text, num_flashcards=10):
    """
    Generate flashcards using Google Gemini (FREE, cloud-based, very capable!)
    Works on all cloud platforms - great alternative to Groq!
    """
    try:
        # Use google.generativeai (stable, works reliably)
        try:
            import google.generativeai as genai
        except ImportError:
            print("[ERROR] Google Generative AI library not installed. Install with: pip install google-generativeai")
            return None
        
        # Check if API key is configured
        api_key = getattr(settings, 'GEMINI_API_KEY', '')
        if not api_key or not isinstance(api_key, str) or api_key.strip() == '':
            print("[WARNING] Gemini API key not found - falling back to other methods")
            return None
        
        model_name = getattr(settings, 'GEMINI_MODEL', 'gemini-pro')
        print(f"[INFO] Using Gemini LLM: {model_name} for flashcard generation")
        
        # Configure Gemini - use old API for now (new API has compatibility issues)
        # Old API (google.generativeai) - works reliably
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name)
        
        # Truncate text if too long
        max_chars = 8000  # Leave room for prompt
        if len(text) > max_chars:
            text = text[:max_chars] + "..."
        
        prompt = f"""You are creating {num_flashcards} educational flashcards with CONCISE answers containing key points.

CRITICAL REQUIREMENT - YOU MUST FOLLOW THIS:
**ALL ANSWERS MUST ONLY USE INFORMATION FROM THE TEXT PROVIDED BELOW. DO NOT use any external knowledge, general knowledge, or information from your training data. If information is not in the text, do not include it in the answer.**

STRICT REQUIREMENTS - FOLLOW THESE EXACTLY:
1. Each answer MUST be CONCISE (up to 150 words maximum) - summarize key points clearly
2. Questions MUST test understanding - use "How", "Why", "Explain", "Compare", "What are the key differences"
3. NEVER create simple "What is X?" questions with one-word answers
4. Focus on: key processes, main differences, essential relationships, critical applications
5. Answers should be brief but informative - cover main concepts without excessive detail
6. **ONLY use information that is explicitly stated or clearly implied in the text below**
7. **DO NOT add information from your general knowledge - stick strictly to the provided text**

Text content from uploaded document:
{text}

Generate exactly {num_flashcards} flashcards in JSON format with "question" and "answer" fields.

REQUIRED FORMAT - Answers must be CONCISE and summarized:
- Question types: "How does...", "Explain why...", "What are the key differences...", "Compare...", "What are the main steps..."
- Answers: Concise summaries with key points (up to 150 words, NOT lengthy explanations)
- **Answers must ONLY contain information from the text above - no external knowledge**

EXAMPLES OF WHAT TO CREATE (based on text content):
{{"question": "How does [process from text] work?", "answer": "[Answer using ONLY information from the text above]"}}

{{"question": "What are the key differences between [concepts from text]?", "answer": "[Answer using ONLY information from the text above]"}}

EXAMPLES OF WHAT NOT TO CREATE (REJECT THESE):
- {{"question": "What is DNA?", "answer": "Genetic material."}}  ❌ TOO SIMPLE
- {{"question": "Define respiration.", "answer": "A process."}}  ❌ TOO SIMPLE  
- Answers using information NOT in the text  ❌ WRONG - ONLY use text content
- Long answers over 150 words  ❌ TOO LENGTHY

Generate ONLY concise flashcards with summarized answers (up to 150 words) using ONLY information from the text provided. Return ONLY the JSON array."""
        
        # Generate with Gemini
        try:
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.9,
                    max_output_tokens=4000,
                )
            )
            content = response.text.strip()
        except Exception as api_error:
            error_str = str(api_error).lower()
            if '404' in error_str or 'not found' in error_str or 'not supported' in error_str:
                print(f"[ERROR] Gemini model '{model_name}' not found or not supported: {str(api_error)}")
                print("[INFO] Try using a different model like 'gemini-pro' or check available models.")
            raise api_error
        
        # Remove markdown code blocks if present
        if content.startswith('```'):
            lines = content.split('\n')
            content = '\n'.join(lines[1:-1]) if lines[-1].startswith('```') else '\n'.join(lines[1:])
        
        # Try to extract JSON from response
        start_idx = content.find('[')
        end_idx = content.rfind(']') + 1
        
        if start_idx != -1 and end_idx > start_idx:
            content = content[start_idx:end_idx]
        
        # Parse JSON (with error recovery like Groq)
        flashcards = None
        try:
            flashcards = json.loads(content)
        except json.JSONDecodeError as json_error:
            print(f"[WARNING] Initial JSON parse failed: {str(json_error)}")
            print("[INFO] Attempting to fix malformed JSON...")
            
            # Try to fix unterminated strings by finding the last complete flashcard
            try:
                import re
                # Pattern to match complete flashcard objects
                pattern = r'\{"question"\s*:\s*"([^"]*(?:\\.[^"]*)*)"\s*,\s*"answer"\s*:\s*"([^"]*(?:\\.[^"]*)*)"\s*\}'
                matches = re.findall(pattern, content)
                
                if matches:
                    flashcards = []
                    for question, answer in matches:
                        # Unescape JSON strings
                        question = question.replace('\\"', '"').replace('\\n', '\n').replace('\\\\', '\\')
                        answer = answer.replace('\\"', '"').replace('\\n', '\n').replace('\\\\', '\\')
                        flashcards.append({'question': question, 'answer': answer})
                    print(f"[INFO] Extracted {len(flashcards)} flashcards from malformed JSON")
                else:
                    # Try to find complete objects by looking for balanced braces
                    brace_count = 0
                    last_valid_pos = 0
                    for i, char in enumerate(content):
                        if char == '{':
                            brace_count += 1
                        elif char == '}':
                            brace_count -= 1
                            if brace_count == 0:
                                last_valid_pos = i + 1
                    
                    if last_valid_pos > 0:
                        # Try parsing up to the last valid position
                        partial_content = content[:last_valid_pos]
                        # Ensure it's a valid array
                        if partial_content.startswith('[') and not partial_content.rstrip().endswith(']'):
                            partial_content = '[' + partial_content + ']'
                        try:
                            flashcards = json.loads(partial_content)
                            print(f"[INFO] Parsed partial JSON (up to position {last_valid_pos})")
                        except:
                            pass
            except Exception as fix_error:
                print(f"[WARNING] JSON fix attempt failed: {str(fix_error)}")
            
            # If still no flashcards, raise the original error
            if not flashcards:
                raise json_error
        
        # Validate and format - filter out simple/short flashcards (same as Groq)
        if isinstance(flashcards, list):
            formatted_flashcards = []
            for card in flashcards:
                if isinstance(card, dict) and 'question' in card and 'answer' in card:
                    question = str(card['question']).strip()
                    answer = str(card['answer']).strip()
                    
                    # Filter out simple flashcards
                    # Skip if answer is too short (less than 20 characters)
                    if len(answer) < 20:
                        print(f"[FILTER] Skipping flashcard - answer too short: {question[:50]}...")
                        continue
                    
                    # Skip if answer has too few words (need at least 5 words for meaningful answer)
                    answer_words = answer.split()
                    if len(answer_words) < 5:
                        print(f"[FILTER] Skipping flashcard - answer too simple ({len(answer_words)} words): {question[:50]}...")
                        continue
                    
                    # Skip if answer is too long (over 150 words - should be concise!)
                    if len(answer_words) > 150:
                        print(f"[FILTER] Skipping flashcard - answer too lengthy ({len(answer_words)} words, max 150): {question[:50]}...")
                        continue
                    
                    # Skip if question is too simple (just "What is X?" or "Define X") with very short answer
                    question_lower = question.lower()
                    if (question_lower.startswith('what is ') and len(question.split()) < 4) or \
                       (question_lower.startswith('define ') and len(question.split()) < 3):
                        # Check if answer is also too short/simple
                        if len(answer_words) < 8:
                            print(f"[FILTER] Skipping flashcard - too simple question/answer: {question[:50]}...")
                            continue
                    
                    formatted_flashcards.append({
                        'question': question,
                        'answer': answer
                    })
            
            if len(formatted_flashcards) < num_flashcards * 0.5:
                print(f"[WARNING] Only {len(formatted_flashcards)}/{num_flashcards} flashcards passed quality filter")
                if len(formatted_flashcards) == 0:
                    return None
            
            print(f"[SUCCESS] {len(formatted_flashcards)} comprehensive flashcards generated using Gemini")
            return formatted_flashcards if formatted_flashcards else None
        
        return None
        
    except ImportError:
        print("[ERROR] Google Generative AI library not installed. Install with: pip install google-generativeai")
        return None
    except json.JSONDecodeError as e:
        print(f"[ERROR] Gemini JSON decode error: {str(e)}. Response may be malformed.")
        return None
    except Exception as e:
        error_str = str(e).lower()
        
        if 'quota' in error_str or 'rate limit' in error_str or '429' in error_str:
            print(f"[ERROR] Gemini quota/rate limit exceeded: {str(e)}")
        elif '401' in error_str or 'unauthorized' in error_str or 'invalid' in error_str and 'key' in error_str:
            print(f"[ERROR] Gemini API key invalid or unauthorized: {str(e)}")
        else:
            print(f"[ERROR] Gemini generation error: {str(e)}")
        
        print("[INFO] Falling back to other LLM providers or rule-based generation.")
        return None


def generate_flashcards_with_llm(text, num_flashcards=10):
    """
    Generate flashcards using the configured LLM provider
    Prioritizes cloud LLMs (Groq, Gemini) - skips Ollama in production/cloud
    """
    provider = getattr(settings, 'LLM_PROVIDER', 'groq').lower()
    debug_mode = getattr(settings, 'DEBUG', False)
    use_llm = getattr(settings, 'USE_LLM', True)
    
    print(f"[DEBUG] LLM Configuration - Provider: {provider}, USE_LLM: {use_llm}, DEBUG: {debug_mode}")
    
    # Check if LLM is enabled
    if not use_llm:
        print("[WARNING] USE_LLM is False - skipping LLM generation")
        return None
    
    # In production/cloud, NEVER use Ollama - force cloud LLMs
    if not debug_mode and provider == 'ollama':
        print("[WARNING] Ollama is local-only and won't work on cloud platforms!")
        print("[INFO] Forcing cloud LLM (Groq/Gemini) instead of Ollama...")
        provider = 'groq'  # Force to cloud LLM
    
    # Try configured provider first (if it's a cloud LLM)
    if provider == 'groq':
        print(f"[INFO] Attempting to generate {num_flashcards} flashcards using Groq (cloud LLM)...")
        groq_result = generate_flashcards_with_groq(text, num_flashcards)
        if groq_result:
            print(f"[SUCCESS] Generated {len(groq_result)} flashcards using Groq!")
            return groq_result
        else:
            print("[WARNING] Groq generation failed - trying Gemini as fallback...")
    
    if provider == 'gemini':
        print(f"[INFO] Attempting to generate {num_flashcards} flashcards using Gemini (cloud LLM)...")
        gemini_result = generate_flashcards_with_gemini(text, num_flashcards)
        if gemini_result:
            print(f"[SUCCESS] Generated {len(gemini_result)} flashcards using Gemini!")
            return gemini_result
        else:
            print("[WARNING] Gemini generation failed - trying Groq...")
            # Fallback to Groq
            groq_result = generate_flashcards_with_groq(text, num_flashcards)
            if groq_result:
                return groq_result
    
    # Try cloud LLMs as fallback (prioritize cloud over local)
    if provider != 'groq':
        print(f"[INFO] Attempting to generate {num_flashcards} flashcards using Groq (cloud LLM)...")
        groq_result = generate_flashcards_with_groq(text, num_flashcards)
        if groq_result:
            print(f"[SUCCESS] Generated {len(groq_result)} flashcards using Groq!")
            return groq_result
    
    if provider != 'gemini':
        print(f"[INFO] Attempting to generate {num_flashcards} flashcards using Gemini (cloud LLM)...")
        gemini_result = generate_flashcards_with_gemini(text, num_flashcards)
        if gemini_result:
            print(f"[SUCCESS] Generated {len(gemini_result)} flashcards using Gemini!")
            return gemini_result
    
    # Only try Ollama in DEBUG mode (local development)
    if provider == 'ollama' and debug_mode:
        print("[INFO] Using Ollama (local development only)...")
        ollama_result = generate_flashcards_with_ollama(text, num_flashcards)
        if ollama_result:
            return ollama_result
        else:
            # If Ollama fails, try cloud LLMs
            print("[INFO] Ollama failed. Trying cloud LLMs...")
            groq_result = generate_flashcards_with_groq(text, num_flashcards)
            if groq_result:
                return groq_result
            gemini_result = generate_flashcards_with_gemini(text, num_flashcards)
            if gemini_result:
                return gemini_result
    
    # No LLM available or failed
    print("[INFO] Using rule-based flashcard generation (no LLM)")
    return None


def generate_flashcards_from_text(text, num_flashcards=10):
    """
    Generate flashcards from text content
    Uses LLM if available and enabled, otherwise falls back to rule-based generation
    """
    # Try LLM first if enabled
    use_llm = getattr(settings, 'USE_LLM', True)
    if use_llm:
        llm_flashcards = generate_flashcards_with_llm(text, num_flashcards)
        if llm_flashcards:
            return llm_flashcards
    
    # Fallback to rule-based generation
    flashcards = []
    
    if not text or len(text.strip()) == 0:
        return flashcards
    
    # Split text into sentences
    sentences = text.replace('!', '.').replace('?', '.').split('.')
    sentences = [s.strip() for s in sentences if len(s.strip()) > 30]
    
    # Create flashcards from sentences
    # Simple approach: use sentence as answer, create question from key terms
    for i, sentence in enumerate(sentences[:num_flashcards]):
        if len(sentence) < 30:
            continue
        
        # Extract key terms (words longer than 4 characters, capitalized)
        words = sentence.split()
        key_terms = [w.strip('.,!?;:') for w in words if len(w.strip('.,!?;:')) > 4]
        
        if len(key_terms) > 0:
            # Create a question by asking about the main concept
            main_term = key_terms[0] if key_terms else "this concept"
            question = f"What is {main_term}?"
            
            # Use the sentence as the answer
            answer = sentence
            
            flashcards.append({
                'question': question,
                'answer': answer
            })
    
    # If we don't have enough flashcards, create more from remaining sentences
    if len(flashcards) < num_flashcards and len(sentences) > len(flashcards):
        remaining = sentences[len(flashcards):]
        for sentence in remaining[:num_flashcards - len(flashcards)]:
            if len(sentence) > 30:
                # Create definition-style flashcards
                words = sentence.split()
                if len(words) > 5:
                    # First few words as question, rest as answer
                    question_words = words[:3]
                    answer_words = words[3:]
                    question = f"Explain: {' '.join(question_words)}"
                    answer = ' '.join(answer_words)
                    
                    flashcards.append({
                        'question': question,
                        'answer': answer
                    })
    
    return flashcards

