from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.files.base import ContentFile
from django.conf import settings
import mimetypes
import io
import os
from PIL import Image

from .models import UploadedFile, FlashcardSet, Flashcard
from .file_processor import extract_text_from_file, summarize_text, generate_flashcards_from_text, calculate_flashcard_count, extract_first_image_from_pdf, extract_first_image_from_docx, extract_all_images_from_pdf, extract_all_images_from_docx, match_images_to_flashcards, extract_all_images_from_pdf, extract_all_images_from_docx, understand_image_with_vision
from .visual_region_service import VisualRegionPipeline
from django.http import JsonResponse
from django.db import connection


def index(request):
    """Home page with file upload"""
    recent_files = UploadedFile.objects.all()[:5]
    recent_sets = FlashcardSet.objects.all()[:5]
    
    # Debug: Show LLM configuration (only in DEBUG mode)
    debug_info = {}
    if getattr(settings, 'DEBUG', False):
        debug_info = {
            'llm_provider': getattr(settings, 'LLM_PROVIDER', 'not set'),
            'use_llm': getattr(settings, 'USE_LLM', 'not set'),
            'groq_key_set': bool(getattr(settings, 'GROQ_API_KEY', '').strip()),
            'groq_key_length': len(getattr(settings, 'GROQ_API_KEY', '')),
        }
    
    return render(request, 'flashcards/index.html', {
        'recent_files': recent_files,
        'recent_sets': recent_sets,
        'debug_info': debug_info,
    })


def upload_file(request):
    """Handle file upload and processing"""
    if request.method == 'POST':
        if 'file' not in request.FILES:
            messages.error(request, 'No file selected.')
            return redirect('index')
        
        uploaded_file = request.FILES['file']
        file_type = uploaded_file.content_type or mimetypes.guess_type(uploaded_file.name)[0] or 'application/octet-stream'
        
        # Save the file
        file_obj = UploadedFile(
            user=request.user if request.user.is_authenticated else None,
            filename=uploaded_file.name,
            file_type=file_type
        )
        file_obj.file.save(uploaded_file.name, ContentFile(uploaded_file.read()), save=True)
        
        # Process the file
        try:
            file_path = file_obj.file.path
            text = extract_text_from_file(file_path, file_type)
            
            # For images, allow shorter content (OCR + vision description combined)
            min_length = 30 if file_type.startswith('image/') else 50
            if not text or len(text.strip()) < min_length:
                messages.warning(request, 'File processed but contains very little extractable content.')
                file_obj.summary = "File contains minimal extractable content."
            else:
                # Generate summary
                summary = summarize_text(text)
                file_obj.summary = summary
                file_obj.processed = True
                file_obj.save()
                
                # Calculate optimal number of flashcards based on content
                num_flashcards = calculate_flashcard_count(text)
                
                # Generate flashcards with dynamic count
                flashcards_data = generate_flashcards_from_text(text, num_flashcards=num_flashcards)
                
                if flashcards_data:
                    # Create flashcard set
                    flashcard_set = FlashcardSet.objects.create(
                        file=file_obj,
                        title=f"Flashcards from {file_obj.filename}"
                    )
                    
                    # Use visual region pipeline for intelligent cropping (PDF/Word only)
                    is_image_file = file_type.startswith('image/')
                    
                    # Try visual region pipeline first, but always fall back to standard extraction if it fails
                    # COMPREHENSIVE FIX: Make visual region matching completely safe and optional
                    use_visual_regions = False
                    region_matches = []
                    
                    # Check if visual region matching is enabled (can be disabled via env var for safety)
                    enable_visual_regions = getattr(settings, 'ENABLE_VISUAL_REGIONS', True)
                    
                    if not enable_visual_regions:
                        print("[INFO] Visual region matching is disabled, using standard image extraction")
                    elif not is_image_file and (file_type == 'application/pdf' or file_path.endswith('.pdf') or
                                             file_type in ['application/vnd.openxmlformats-officedocument.wordprocessingml.document', 
                                                          'application/msword'] or file_path.endswith(('.docx', '.doc'))):
                        # Wrap entire visual region pipeline in comprehensive error handling
                        try:
                            # Extract questions for matching
                            questions = [card['question'] for card in flashcards_data]
                            
                            # Add timeout protection using signal (if available) or just try-catch
                            print("[INFO] Attempting visual region matching (with automatic fallback on any error)...")
                            
                            try:
                                pipeline = VisualRegionPipeline()
                                region_matches = pipeline.process_document(file_path, file_type, questions)
                                
                                if region_matches and len(region_matches) > 0:
                                    # Check if any matches are semantic (not all fallback)
                                    semantic_matches = [m for m in region_matches if len(m) > 2 and m[2] != 0.5]
                                    if semantic_matches:
                                        print(f"[INFO] Visual region pipeline matched {len(semantic_matches)} semantic matches out of {len(region_matches)} total")
                                        use_visual_regions = True
                                    else:
                                        print(f"[INFO] Visual region pipeline only found fallback matches (no semantic matches), using standard image extraction")
                                        use_visual_regions = False
                                        region_matches = []
                                else:
                                    print(f"[INFO] Visual region pipeline found no matches, using standard image extraction")
                                    use_visual_regions = False
                                    
                            except KeyboardInterrupt:
                                # Don't catch keyboard interrupt, let it propagate
                                raise
                            except (MemoryError, RuntimeError, SystemExit, OSError, ImportError) as critical_err:
                                print(f"[WARNING] Critical error in visual region pipeline: {type(critical_err).__name__}: {str(critical_err)}")
                                print("[INFO] Falling back to standard image extraction")
                                use_visual_regions = False
                                region_matches = []
                            except Exception as e:
                                print(f"[WARNING] Unexpected error in visual region pipeline: {type(e).__name__}: {str(e)}")
                                print("[INFO] Falling back to standard image extraction")
                                use_visual_regions = False
                                region_matches = []
                            
                        except Exception as outer_err:
                            # Catch-all for any errors in the outer try block
                            print(f"[WARNING] Error setting up visual region pipeline: {type(outer_err).__name__}: {str(outer_err)}")
                            print("[INFO] Falling back to standard image extraction")
                            use_visual_regions = False
                            region_matches = []
                    else:
                        print("[INFO] File type not supported for visual region matching, using standard image extraction")
                    
                    # If visual regions worked, use them; otherwise use standard image extraction
                    if use_visual_regions:
                        # Create flashcards with matched visual regions
                        for idx, card_data in enumerate(flashcards_data):
                            flashcard = Flashcard.objects.create(
                                flashcard_set=flashcard_set,
                                question=card_data['question'],
                                answer=card_data['answer'],
                                source_image=None  # Visual regions are stored in cropped_image
                            )
                            
                            # Find matching region for this question
                            matched_region = None
                            confidence = 0.0
                            for q_idx, region, conf in region_matches:
                                if q_idx == idx:
                                    matched_region = region
                                    confidence = conf
                                    break
                            
                            # Save cropped region if found and confidence is high enough
                            # Skip fallback matches (confidence == 0.5) - don't display irrelevant images
                            # Lowered threshold to 0.15 (15%) to allow more images to be displayed
                            if matched_region and matched_region.image and confidence >= 0.15 and confidence != 0.5:
                                try:
                                    # Save cropped region image
                                    img_buffer = io.BytesIO()
                                    matched_region.image.save(img_buffer, format='PNG')
                                    img_buffer.seek(0)
                                    
                                    filename = f"flashcard_{flashcard.id}_region_{matched_region.region_type}.png"
                                    flashcard.cropped_image.save(
                                        filename,
                                        ContentFile(img_buffer.getvalue()),
                                        save=True
                                    )
                                    # Explicitly save the flashcard to ensure the image field is persisted
                                    flashcard.save()
                                    print(f"[SUCCESS] Saved {matched_region.region_type} region for flashcard {idx+1} (confidence: {confidence:.2f}, type: SEMANTIC)")
                                    print(f"[DEBUG] Flashcard {flashcard.id} cropped_image saved: {flashcard.cropped_image.name}, exists: {flashcard.cropped_image.name and flashcard.cropped_image.storage.exists(flashcard.cropped_image.name) if flashcard.cropped_image.name else False}")
                                except Exception as e:
                                    print(f"[WARNING] Failed to save region for flashcard {idx+1}: {str(e)}")
                            else:
                                if matched_region:
                                    if confidence == 0.5:
                                        print(f"[INFO] Skipped fallback match for flashcard {idx+1} - no image displayed (fallback matches are not semantically relevant)")
                                    else:
                                        print(f"[INFO] Skipped region for flashcard {idx+1} (low confidence: {confidence:.2f})")
                        
                        # Skip the old image matching logic
                        word_count = len(text.split())
                        messages.success(request, f'File processed successfully! Created {len(flashcards_data)} flashcards from {word_count:,} words of content.')
                        return redirect('view_flashcards', set_id=flashcard_set.id)
                    
                    # Fallback to standard image matching for image files or if visual region pipeline fails/finds no matches
                    print(f"[INFO] Using standard image extraction (visual_regions={use_visual_regions})")
                    # Determine if source file is an image or contains extractable images
                    is_image_file = file_type.startswith('image/')
                    extracted_image_files = []
                    
                    # Try to extract all images from PDF/Word documents
                    if not is_image_file:
                        try:
                            images = []
                            if file_type == 'application/pdf' or file_path.endswith('.pdf'):
                                images = extract_all_images_from_pdf(file_path)
                                print(f"[INFO] Extracted {len(images)} pages/images from PDF")
                            
                            elif file_type in ['application/vnd.openxmlformats-officedocument.wordprocessingml.document', 
                                              'application/msword'] or file_path.endswith(('.docx', '.doc')):
                                images = extract_all_images_from_docx(file_path)
                                print(f"[INFO] Extracted {len(images)} images from Word document")
                            
                            # Save all extracted images as UploadedFile records
                            for idx, img in enumerate(images):
                                img_buffer = io.BytesIO()
                                img.save(img_buffer, format='PNG')
                                img_buffer.seek(0)
                                
                                extracted_image_file = UploadedFile(
                                    user=file_obj.user,
                                    filename=f"{file_obj.filename}_img_{idx+1}.png",
                                    file_type='image/png'
                                )
                                extracted_image_file.file.save(
                                    f"{file_obj.filename}_img_{idx+1}.png",
                                    ContentFile(img_buffer.getvalue()),
                                    save=True
                                )
                                extracted_image_file.processed = True
                                extracted_image_file.save()
                                extracted_image_files.append(extracted_image_file)
                                print(f"[INFO] Saved extracted image {idx+1}/{len(images)}: {extracted_image_file.filename}")
                                
                        except Exception as e:
                            print(f"[WARNING] Failed to extract images from document: {str(e)}")
                            extracted_image_files = []
                    else:
                        # Single image file - use it directly
                        extracted_image_files = [file_obj]
                    
                    # Match images to flashcards
                    image_matches = None
                    if extracted_image_files and len(extracted_image_files) > 0:
                        print(f"[INFO] Matching {len(extracted_image_files)} images to {len(flashcards_data)} flashcards...")
                        image_matches = match_images_to_flashcards(flashcards_data, extracted_image_files, text)
                        if image_matches:
                            print(f"[INFO] Successfully matched images to flashcards")
                            # Create a mapping dictionary for easier lookup
                            match_dict = {q_idx: img_idx for q_idx, img_idx in image_matches}
                            print(f"[INFO] Match dictionary: {match_dict}")
                        else:
                            # Fallback: distribute images in round-robin fashion instead of using first image for all
                            print(f"[INFO] Image matching failed or returned None - distributing images in round-robin fashion")
                            match_dict = {i: i % len(extracted_image_files) for i in range(len(flashcards_data))}
                            print(f"[INFO] Round-robin distribution: {match_dict}")
                    else:
                        match_dict = {}
                    
                    # Helper function to check if image is blank/white
                    def is_image_blank(image_file):
                        """Check if an image is mostly blank/white"""
                        try:
                            from PIL import Image
                            import numpy as np
                            
                            # Open and check the image
                            img = Image.open(image_file.file)
                            if img.mode != 'RGB':
                                img = img.convert('RGB')
                            
                            # Convert to numpy array
                            img_array = np.array(img)
                            
                            # Check if image is mostly white (>95% white pixels)
                            # White pixels are those with RGB values all > 240
                            white_pixels = np.sum(np.all(img_array > 240, axis=2))
                            total_pixels = img_array.shape[0] * img_array.shape[1]
                            white_ratio = white_pixels / total_pixels if total_pixels > 0 else 0
                            
                            # Also check if image has very low variance (uniform color)
                            variance = np.var(img_array)
                            
                            # Image is blank if >95% white OR very low variance (<100)
                            is_blank = white_ratio > 0.95 or variance < 100
                            
                            if is_blank:
                                print(f"[WARNING] Image {image_file.filename} appears to be blank (white_ratio: {white_ratio:.2f}, variance: {variance:.1f})")
                            
                            return is_blank
                        except Exception as e:
                            print(f"[WARNING] Could not check if image is blank: {str(e)}")
                            return False  # Assume not blank if we can't check
                    
                    # Create flashcards with matched images
                    for idx, card_data in enumerate(flashcards_data):
                        # Determine which image to use for this flashcard
                        matched_image = None
                        if match_dict and idx in match_dict:
                            img_idx = match_dict[idx]
                            if img_idx < len(extracted_image_files):
                                candidate_image = extracted_image_files[img_idx]
                                # Check if image is blank, if so try next images
                                if not is_image_blank(candidate_image):
                                    matched_image = candidate_image
                                    print(f"[INFO] Flashcard {idx+1} assigned to image {img_idx+1} ({candidate_image.filename})")
                                else:
                                    # Try to find a non-blank image
                                    print(f"[WARNING] Assigned image {img_idx+1} is blank, searching for alternative...")
                                    for alt_idx in range(len(extracted_image_files)):
                                        alt_image = extracted_image_files[(img_idx + alt_idx + 1) % len(extracted_image_files)]
                                        if not is_image_blank(alt_image):
                                            matched_image = alt_image
                                            print(f"[INFO] Flashcard {idx+1} using alternative image {extracted_image_files.index(alt_image)+1} ({alt_image.filename})")
                                            break
                        
                        # Fallback: distribute in round-robin if no match
                        if not matched_image and extracted_image_files:
                            # Use round-robin distribution, but skip blank images
                            for offset in range(len(extracted_image_files)):
                                img_idx = (idx + offset) % len(extracted_image_files)
                                candidate_image = extracted_image_files[img_idx]
                                if not is_image_blank(candidate_image):
                                    matched_image = candidate_image
                                    print(f"[INFO] Flashcard {idx+1} fallback: using image {img_idx+1} ({candidate_image.filename})")
                                    break
                        
                        # Create flashcard
                        Flashcard.objects.create(
                            flashcard_set=flashcard_set,
                            question=card_data['question'],
                            answer=card_data['answer'],
                            source_image=matched_image
                        )
                    
                    word_count = len(text.split())
                    messages.success(request, f'File processed successfully! Created {len(flashcards_data)} flashcards from {word_count:,} words of content.')
                    return redirect('view_flashcards', set_id=flashcard_set.id)
                else:
                    messages.warning(request, 'File processed but could not generate flashcards.')
            
            file_obj.save()
            return redirect('view_file', file_id=file_obj.id)
            
        except Exception as e:
            # Safely encode error message to avoid Unicode encoding issues
            error_msg = str(e)
            try:
                # Try to encode to ensure it's safe for display
                error_msg.encode('ascii', errors='replace')
            except:
                error_msg = "Error processing file: Unable to process file (encoding issue)"
            messages.error(request, f'Error processing file: {error_msg}')
            file_obj.delete()
            return redirect('index')
    
    return redirect('index')


def view_file(request, file_id):
    """View uploaded file details"""
    file_obj = get_object_or_404(UploadedFile, id=file_id)
    flashcard_sets = file_obj.flashcard_sets.all()
    return render(request, 'flashcards/view_file.html', {
        'file_obj': file_obj,
        'flashcard_sets': flashcard_sets
    })


def view_flashcards(request, set_id):
    """View flashcards in a set"""
    flashcard_set = get_object_or_404(FlashcardSet, id=set_id)
    flashcards = flashcard_set.flashcards.all()
    
    # Check if the source file is an image (for backwards compatibility with old flashcards)
    # Handle case where file or file_type might be None
    try:
        source_file_is_image = flashcard_set.file.file_type.startswith('image/') if (flashcard_set.file and flashcard_set.file.file_type) else False
    except (AttributeError, Exception):
        source_file_is_image = False
    
    # Debug: Log image information for each flashcard
    for flashcard in flashcards:
        flashcard.display_image = flashcard.get_display_image()
        # Debug logging
        if flashcard.cropped_image:
            print(f"[DEBUG] Flashcard {flashcard.id} has cropped_image: {flashcard.cropped_image.name}, URL: {flashcard.cropped_image.url if flashcard.cropped_image else 'N/A'}")
        elif flashcard.source_image:
            print(f"[DEBUG] Flashcard {flashcard.id} has source_image: {flashcard.source_image.filename}")
        else:
            print(f"[DEBUG] Flashcard {flashcard.id} has no image")
    
    return render(request, 'flashcards/view_flashcards.html', {
        'flashcard_set': flashcard_set,
        'flashcards': flashcards,
        'source_file_is_image': source_file_is_image,
    })


def list_files(request):
    """List all uploaded files"""
    files = UploadedFile.objects.all().order_by('-uploaded_at')
    return render(request, 'flashcards/list_files.html', {
        'files': files
    })


def list_flashcard_sets(request):
    """List all flashcard sets"""
    sets = FlashcardSet.objects.all().order_by('-created_at')
    return render(request, 'flashcards/list_sets.html', {
        'flashcard_sets': sets
    })


def health_check(request):
    """Health check endpoint for Railway and other platforms"""
    try:
        # Test database connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return JsonResponse({
            'status': 'healthy',
            'database': 'connected'
        }, status=200)
    except Exception as e:
        return JsonResponse({
            'status': 'unhealthy',
            'error': str(e)
        }, status=503)


