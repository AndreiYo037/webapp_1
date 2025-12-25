from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.files.base import ContentFile
from django.conf import settings
import mimetypes

from .models import UploadedFile, FlashcardSet, Flashcard
from .file_processor import extract_text_from_file, summarize_text, generate_flashcards_from_text, calculate_flashcard_count


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
                    
                    # Create flashcards
                    for card_data in flashcards_data:
                        Flashcard.objects.create(
                            flashcard_set=flashcard_set,
                            question=card_data['question'],
                            answer=card_data['answer']
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
    return render(request, 'flashcards/view_flashcards.html', {
        'flashcard_set': flashcard_set,
        'flashcards': flashcards
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
