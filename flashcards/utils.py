"""Utility functions for processing files and generating flashcards"""
import os
from django.conf import settings


def process_file(file_upload):
    """
    Extract text content from uploaded file.
    Supports: .txt, .pdf, .docx, .md files
    """
    file_path = file_upload.file.path
    file_extension = file_upload.get_file_extension()
    
    try:
        if file_extension == '.txt' or file_extension == '.md':
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        
        elif file_extension == '.pdf':
            try:
                import PyPDF2
                with open(file_path, 'rb') as f:
                    pdf_reader = PyPDF2.PdfReader(f)
                    text = ''
                    for page in pdf_reader.pages:
                        text += page.extract_text() + '\n'
                    return text
            except ImportError:
                raise Exception("PyPDF2 is required for PDF processing. Install it with: pip install PyPDF2")
        
        elif file_extension in ['.docx', '.doc']:
            try:
                from docx import Document
                doc = Document(file_path)
                text = '\n'.join([paragraph.text for paragraph in doc.paragraphs])
                return text
            except ImportError:
                raise Exception("python-docx is required for DOCX processing. Install it with: pip install python-docx")
        
        else:
            raise Exception(f"Unsupported file type: {file_extension}. Supported types: .txt, .md, .pdf, .docx")
    
    except Exception as e:
        raise Exception(f"Error reading file: {str(e)}")


def generate_flashcards(text_content, num_cards=10):
    """
    Generate flashcards from text content.
    Uses simple sentence-based approach to create Q&A pairs.
    For production, you might want to use AI/ML for better card generation.
    """
    if not text_content or not text_content.strip():
        raise Exception("File is empty or contains no text")
    
    # Split text into sentences
    import re
    sentences = re.split(r'[.!?]+\s+', text_content)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 20]  # Filter short sentences
    
    if len(sentences) < 2:
        raise Exception("Not enough content to generate flashcards. File needs more text.")
    
    flashcards = []
    
    # Simple approach: Use every other sentence as question/answer pairs
    # Or create fill-in-the-blank style questions
    for i in range(0, min(len(sentences) - 1, num_cards), 2):
        if i + 1 < len(sentences):
            question = f"What comes after: {sentences[i][:100]}..."
            answer = sentences[i + 1]
        else:
            # Create a fill-in-the-blank question
            words = sentences[i].split()
            if len(words) > 5:
                blank_index = len(words) // 2
                question = ' '.join(words[:blank_index]) + " _____ " + ' '.join(words[blank_index+1:])
                answer = words[blank_index]
            else:
                question = f"Explain: {sentences[i][:100]}"
                answer = sentences[i]
        
        flashcards.append({
            'question': question[:500],  # Limit length
            'answer': answer[:500]
        })
    
    # If we don't have enough cards, create more from remaining sentences
    if len(flashcards) < num_cards:
        remaining = sentences[len(flashcards) * 2:]
        for i, sentence in enumerate(remaining[:num_cards - len(flashcards)]):
            # Create definition-style questions
            words = sentence.split()
            if len(words) > 3:
                key_word = words[0] if words[0][0].isupper() else words[len(words)//2]
                question = f"What is {key_word}?"
                answer = sentence
            else:
                question = f"Complete: {sentence[:80]}..."
                answer = sentence
            
            flashcards.append({
                'question': question[:500],
                'answer': answer[:500]
            })
    
    return flashcards[:num_cards]  # Return up to num_cards

