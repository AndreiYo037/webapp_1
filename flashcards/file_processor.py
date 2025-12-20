"""
File processing utilities to extract text from various file types
"""
import os
import json
import requests
import sys
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

        prompt = f"""You are creating {num_flashcards} educational flashcards. These MUST be comprehensive and test deep understanding.

STRICT REQUIREMENTS - FOLLOW THESE EXACTLY:
1. Each answer MUST be at least 50 words (approximately 3-5 sentences)
2. Questions MUST test understanding, not vocabulary - use "How", "Why", "Explain", "Compare", "Analyze", "What are the differences"
3. NEVER create simple "What is X?" questions with one-word answers
4. Focus on: processes, relationships, comparisons, applications, mechanisms, cause-effect
5. Each flashcard should require the learner to explain concepts, not just recall terms

Text content:
{text}

Generate exactly {num_flashcards} flashcards in JSON format with "question" and "answer" fields.

REQUIRED FORMAT - Each answer must be comprehensive:
- Question types to use: "How does...", "Explain why...", "What are the key differences between...", "Compare and contrast...", "Describe the process of...", "Analyze the relationship between..."
- Answers must be detailed explanations (50+ words minimum)

EXAMPLES OF WHAT TO CREATE:
{{"question": "How does the process of cellular respiration convert glucose into ATP, and what are the main stages involved?", "answer": "Cellular respiration converts glucose into ATP through three main stages: glycolysis, the Krebs cycle, and the electron transport chain. In glycolysis, glucose is broken down in the cytoplasm to produce pyruvate and a small amount of ATP. The pyruvate then enters the mitochondria where it's converted to acetyl-CoA for the Krebs cycle, which produces NADH and FADH2. Finally, the electron transport chain uses these electron carriers to create a proton gradient that drives ATP synthesis through chemiosmosis, producing the majority of ATP."}}

{{"question": "What are the key differences between DNA and RNA in terms of structure, function, and location within the cell?", "answer": "DNA and RNA differ in several critical ways. Structurally, DNA is double-stranded with deoxyribose sugar and thymine bases, while RNA is single-stranded with ribose sugar and uracil instead of thymine. Functionally, DNA stores genetic information long-term in the nucleus, while RNA acts as a messenger (mRNA), transfers amino acids (tRNA), and forms ribosomes (rRNA). Location-wise, DNA remains primarily in the nucleus, while RNA is synthesized in the nucleus but functions in both the nucleus and cytoplasm. These differences enable DNA to serve as the stable genetic blueprint while RNA facilitates protein synthesis."}}

EXAMPLES OF WHAT NOT TO CREATE (REJECT THESE):
- {{"question": "What is DNA?", "answer": "Genetic material."}}  ❌ TOO SIMPLE
- {{"question": "Define respiration.", "answer": "A process."}}  ❌ TOO SIMPLE  
- {{"question": "What is ATP?", "answer": "Energy molecule."}}  ❌ TOO SIMPLE

Generate ONLY comprehensive flashcards with detailed answers. Return ONLY the JSON array."""

        try:
            response = client.chat.completions.create(
                model=model,
            messages=[
                {"role": "system", "content": "You are an expert educational content creator. You create CONCISE flashcards with summarized answers (20-40 words) containing only key points. You NEVER create simple vocabulary tests or one-word answers. Answers must be brief summaries with essential information only. You always return valid JSON."},
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
                    
                    # Skip if answer is too long (over 60 words - should be concise!)
                    if len(answer_words) > 60:
                        print(f"[FILTER] Skipping flashcard - answer too lengthy ({len(answer_words)} words, max 60): {question[:50]}...")
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
        
        prompt = f"""You are creating {num_flashcards} educational flashcards with CONCISE, SUMMARIZED answers containing only key points.

STRICT REQUIREMENTS - FOLLOW THESE EXACTLY:
1. Each answer MUST be CONCISE (20-40 words maximum) - summarize key points only
2. Answers should use bullet points or brief sentences covering main concepts
3. Questions MUST test understanding - use "How", "Why", "Explain", "Compare", "What are the key differences"
4. NEVER create simple "What is X?" questions with one-word answers
5. Focus on: key processes, main differences, essential relationships, critical applications

Text content:
{text}

Generate exactly {num_flashcards} flashcards in JSON format with "question" and "answer" fields.

REQUIRED FORMAT - Answers must be CONCISE and summarized:
- Question types: "How does...", "Explain why...", "What are the key differences...", "Compare...", "What are the main steps..."
- Answers: Brief summaries with key points only (20-40 words, NOT lengthy explanations)

EXAMPLES OF WHAT TO CREATE:
{{"question": "How does cellular respiration convert glucose into ATP?", "answer": "Three stages: (1) Glycolysis breaks down glucose in cytoplasm, producing pyruvate and some ATP. (2) Krebs cycle in mitochondria produces NADH/FADH2. (3) Electron transport chain uses these carriers to create ATP via chemiosmosis."}}

{{"question": "What are the key differences between DNA and RNA?", "answer": "DNA: double-stranded, deoxyribose, thymine, stores genetic info in nucleus. RNA: single-stranded, ribose, uracil, functions as mRNA/tRNA/rRNA for protein synthesis. DNA is stable blueprint; RNA is active messenger."}}

EXAMPLES OF WHAT NOT TO CREATE (REJECT THESE):
- {{"question": "What is DNA?", "answer": "Genetic material."}}  ❌ TOO SIMPLE
- {{"question": "Define respiration.", "answer": "A process."}}  ❌ TOO SIMPLE  
- Long answers over 50 words  ❌ TOO LENGTHY

Generate ONLY concise flashcards with summarized key-point answers. Return ONLY the JSON array."""
        
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
                    
                    # Skip if answer is too long (over 60 words - should be concise!)
                    if len(answer_words) > 60:
                        print(f"[FILTER] Skipping flashcard - answer too lengthy ({len(answer_words)} words, max 60): {question[:50]}...")
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

