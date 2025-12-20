"""
File processing utilities to extract text from various file types
"""
import os
import json
import requests
from pathlib import Path
from django.conf import settings


def extract_text_from_file(file_path, file_type):
    """
    Extract text content from various file types
    Returns the extracted text as a string
    """
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
        
        else:
            # Try to read as plain text
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    text = f.read()
            except:
                text = f"Unsupported file type: {file_type}"
    
    except Exception as e:
        text = f"Error processing file: {str(e)}"
    
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
        
        # Check if API key is configured
        api_key = getattr(settings, 'GROQ_API_KEY', '')
        if not api_key:
            print("[WARNING] Groq API key not found - falling back to rule-based generation")
            return None
        
        model = getattr(settings, 'GROQ_MODEL', 'llama-3.3-70b-versatile')
        print(f"[INFO] Using Groq LLM: {model} for flashcard generation")
        
        # Create Groq client (OpenAI-compatible API)
        client = OpenAI(
            api_key=api_key,
            base_url='https://api.groq.com/openai/v1'
        )
        
        # Truncate text if too long
        max_chars = 8000  # Leave room for prompt
        if len(text) > max_chars:
            text = text[:max_chars] + "..."

        prompt = f"""Generate {num_flashcards} high-quality, comprehensive educational flashcards from the following text.

CRITICAL REQUIREMENTS:
- Create flashcards that test UNDERSTANDING and CONCEPTS, not just single words or definitions
- Questions must require thoughtful, detailed answers (at least 2-3 sentences minimum)
- Focus on: relationships, processes, explanations, comparisons, applications, and cause-effect
- Avoid trivial questions that only test vocabulary or single-word facts
- Each question should help the learner understand the material deeply, not just memorize terms

Text content:
{text}

Generate exactly {num_flashcards} comprehensive flashcards in JSON format. Each flashcard must have "question" and "answer" fields.

GOOD examples (use these as inspiration):
- {{"question": "How does photosynthesis convert light energy into chemical energy, and what are the key steps?", "answer": "Photosynthesis converts light energy into chemical energy through two main stages. In the light-dependent reactions, chlorophyll captures light energy which splits water molecules, releasing oxygen and creating ATP and NADPH. In the light-independent reactions (Calvin cycle), these energy carriers are used to combine carbon dioxide into glucose, storing the chemical energy in the glucose molecules."}}
- {{"question": "What are the key differences between mitosis and meiosis, and when is each process used?", "answer": "Mitosis produces two identical diploid cells and is used for growth, repair, and asexual reproduction. Meiosis produces four genetically diverse haploid gametes for sexual reproduction. Key differences: meiosis involves two divisions (meiosis I and II) while mitosis has one; meiosis includes crossing over and independent assortment creating genetic variation; mitosis maintains chromosome number while meiosis halves it."}}

BAD examples (DO NOT create these - they are too simple):
- {{"question": "What is photosynthesis?", "answer": "A process."}}  (too vague, one-word answer)
- {{"question": "Define mitosis.", "answer": "Cell division."}}  (one-word answer, no understanding)

Generate comprehensive flashcards that test deep understanding. Return ONLY the JSON array, no additional text."""

        try:
            response = client.chat.completions.create(
                model=model,
            messages=[
                {"role": "system", "content": "You are an expert educational content creator specializing in comprehensive learning. Your flashcards test deep understanding, concepts, relationships, and applications - not just vocabulary or single-word facts. Always create meaningful questions that require thoughtful, detailed answers. Always return valid JSON."},
                {"role": "user", "content": prompt}
            ],
                temperature=0.8,  # Slightly higher for more creative, comprehensive questions
                max_tokens=3000  # Increased to allow for more detailed answers
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
        
        # Quota/rate limit errors
        if 'quota' in error_str or 'rate limit' in error_str or '429' in error_str:
            print(f"[ERROR] Groq quota/rate limit exceeded: {str(e)}")
            print("[INFO] You may have run out of free tier tokens. Check your Groq dashboard.")
        # Authentication errors
        elif '401' in error_str or 'unauthorized' in error_str or 'invalid' in error_str and 'key' in error_str:
            print(f"[ERROR] Groq API key invalid or unauthorized: {str(e)}")
            print("[INFO] Check your GROQ_API_KEY environment variable.")
        # Model errors
        elif 'model' in error_str and ('not found' in error_str or 'invalid' in error_str):
            print(f"[ERROR] Groq model not available: {str(e)}")
            print("[INFO] The specified model may not be available. Check GROQ_MODEL setting.")
        # Network errors
        elif 'connection' in error_str or 'timeout' in error_str or 'network' in error_str:
            print(f"[ERROR] Groq network/connection error: {str(e)}")
            print("[INFO] Check your internet connection or Groq API status.")
        # Generic error
        else:
            print(f"[ERROR] Groq generation error: {str(e)}")
        
        print("[INFO] Falling back to rule-based flashcard generation.")
        return None


def generate_flashcards_with_llm(text, num_flashcards=10):
    """
    Generate flashcards using the configured LLM provider
    Tries Groq first (free, cloud), then Ollama, then falls back to rule-based
    """
    provider = getattr(settings, 'LLM_PROVIDER', 'groq').lower()
    
    # Try Groq first (free, cloud-based, works everywhere!)
    if provider == 'groq':
        print(f"[INFO] Attempting to generate {num_flashcards} flashcards using Groq...")
        groq_result = generate_flashcards_with_groq(text, num_flashcards)
        if groq_result:
            print(f"[SUCCESS] Generated {len(groq_result)} flashcards using Groq!")
            return groq_result
        else:
            print("[WARNING] Groq generation failed - falling back to rule-based")
    
    # Try Ollama (free, local only)
    if provider == 'ollama':
        ollama_result = generate_flashcards_with_ollama(text, num_flashcards)
        if ollama_result:
            return ollama_result
    
    # No LLM available or failed
    print("ℹ️ Using rule-based flashcard generation (no LLM)")
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

