# Flashcard Generator Web App

A Django-based web application that automatically generates interactive flashcards from uploaded files. Upload PDFs, Word documents, Excel files, or plain text files, and the app will extract content, create summaries, and generate flashcards for studying.

## Features

- 📄 **Multi-format Support**: Upload TXT, PDF, DOC, DOCX, XLS, XLSX files
- 📸 **Image & Diagram Understanding**: Upload images (PNG, JPG, GIF, etc.) with diagrams - uses OCR for text extraction and Groq Vision AI for diagram analysis!
- 📝 **Automatic Summarization**: Extracts and summarizes key content from files
- 🤖 **AI-Powered Flashcard Generation**: Uses Groq (free, cloud LLM) to create high-quality Q&A flashcards - works on all cloud platforms! (with fallback to rule-based generation)
- 🎴 **Smart Flashcard Creation**: Automatically generates educational flashcards from file content based on content length
- 🔄 **Interactive Flashcards**: Flip cards to view questions and answers
- 🎨 **Modern UI**: Beautiful, responsive interface with gradient designs

## Installation

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Install Tesseract OCR (Required for image processing):**
   
   For image and diagram processing, Tesseract OCR is required:
   
   - **Windows**: Download and install from [Tesseract GitHub](https://github.com/UB-Mannheim/tesseract/wiki) or [Direct Download](https://digi.bib.uni-mannheim.de/tesseract/)
   - **Linux (Ubuntu/Debian)**: `sudo apt install tesseract-ocr`
   - **macOS**: `brew install tesseract`
   
   **Note:** The app will still work for text files even without Tesseract, but image processing requires it.

3. **Set up Groq API (Recommended for AI features):**
   
   For AI-powered flashcard generation, use Groq (free, cloud-based, works everywhere!):
   
   a. Get your API key from [Groq Console](https://console.groq.com/keys) (Free and Developer tiers available)
   
   b. Create a `.env` file:
   ```bash
   cp .env.example .env
   ```
   
   c. Edit `.env` and add your API key:
   ```
   GROQ_API_KEY=your_groq_api_key_here
   LLM_PROVIDER=groq
   ```
   
   **Note:** If no API key is set, the app will automatically use rule-based flashcard generation as a fallback.

4. **Set up Groq API for Vision (Recommended for image/diagram understanding):**
   
   The same Groq API key used for flashcard generation also works for image/diagram understanding! Works with both Free and Developer tiers. Just ensure your `.env` has:
   ```
   GROQ_API_KEY=your_groq_api_key_here
   GROQ_VISION_MODEL=llava-v1.5-7b-4096-preview  # Optional: specify vision model
   ```
   
   **Note:** Image processing will use OCR (Tesseract) even without Groq, but Groq Vision provides better diagram understanding.

5. **Run database migrations:**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Create a superuser (optional, for admin access):**
   ```bash
   python manage.py createsuperuser
   ```

7. **Run the development server:**
   ```bash
   python manage.py runserver
   ```

8. **Access the application:**
   - Main app: http://127.0.0.1:8000/
   - Admin panel: http://127.0.0.1:8000/admin/

## Usage

1. **Upload a File:**
   - Go to the home page
   - Click "Upload File" or use the upload area
   - Select a supported file format (text, PDF, Word, Excel, or image)
   - Wait for processing
   - **For images**: The app will extract text using OCR and analyze diagrams using AI vision models

2. **View Flashcards:**
   - After processing, view the generated flashcards
   - Click on cards to flip and see answers
   - Study at your own pace

## Project Structure

```
flashcard_app/
├── flashcard_app/          # Main project settings
│   ├── settings.py          # Django settings
│   ├── urls.py              # Main URL configuration
│   └── wsgi.py              # WSGI configuration
├── flashcards/              # Main app
│   ├── models.py            # Database models
│   ├── views.py             # View functions
│   ├── urls.py              # App URL routes
│   ├── file_processor.py    # File processing utilities
│   └── templates/           # HTML templates
├── media/                   # Uploaded files storage
├── static/                  # Static files (CSS, JS)
├── manage.py                # Django management script
└── requirements.txt         # Python dependencies
```

## Technologies Used

- **Django 4.2+**: Web framework
- **Groq**: Cloud-based LLM for AI-powered flashcard generation and vision analysis (Free and Developer tiers available, works on all platforms!)
- **Tesseract OCR (pytesseract)**: Text extraction from images
- **Ollama**: Alternative free, local LLM option
- **Pillow**: Image processing
- **python-docx**: Word document processing
- **PyPDF2**: PDF text extraction
- **openpyxl**: Excel file processing
- **python-dotenv**: Environment variable management

## How It Works

1. **File Upload**: Files are uploaded and stored in the media directory
2. **Content Extraction**: 
   - **Text Files (TXT, PDF, DOC, DOCX, XLS, XLSX)**: Text is extracted directly
   - **Images (PNG, JPG, GIF, etc.)**: 
     - OCR (Tesseract) extracts any text present in the image
     - AI Vision (Groq) analyzes the diagram structure, relationships, and visual elements
     - Both are combined to create comprehensive content for flashcard generation
3. **Summarization**: Key sentences are extracted to create summaries
4. **Flashcard Generation**: 
   - **With Groq (if configured)**: Uses cloud-based Groq LLM to generate high-quality, contextually relevant Q&A pairs (works on all platforms with Free/Developer tiers!)
   - **With Ollama (if running locally)**: Uses local Ollama LLM (for self-hosted deployments)
   - **Without LLM**: Uses rule-based text processing to create flashcards from sentences
   - **Dynamic Count**: Number of flashcards automatically adjusts based on content length
5. **Interactive Study**: Users can flip through flashcards to study questions and answers

## LLM Configuration

The app uses **Groq** (free, cloud-based) by default for enhanced flashcard generation. Configuration options:

- **LLM_PROVIDER**: Set to `groq` (default, recommended), `ollama` (local only), or `none` for rule-based
- **GROQ_API_KEY**: Your Groq API key (get free at https://console.groq.com/keys) - used for both text and vision analysis
- **GROQ_MODEL**: Text model to use (`llama-3.3-70b-versatile` default, `mixtral-8x7b-32768`, `gemma2-9b-it`)
- **GROQ_VISION_MODEL**: Vision model for images (`llava-v1.5-7b-4096-preview` default)
- **OLLAMA_BASE_URL**: Ollama server URL (only if using Ollama: `http://localhost:11434`)
- **OLLAMA_MODEL**: Ollama model (`mistral`, `llama3`, `gemma`, `phi`, or `qwen`)
- **USE_LLM**: Set to `true` to enable LLM, `false` for rule-based generation

The app automatically falls back to rule-based generation if:
- Groq API key is not set or invalid
- Ollama is not running (if using Ollama)
- API request fails
- `USE_LLM` is set to `false`
- `LLM_PROVIDER` is set to `none`

For image processing:
- **OCR (Tesseract)**: Required for text extraction from images. If not installed, image processing will fail.
- **Groq Vision API**: Optional but recommended for better diagram understanding. Uses the same Groq API key as text generation. If not configured, only OCR text extraction will be used.

## Future Enhancements

- Support for more free LLM providers (Hugging Face)
- AI-powered summarization
- Support for more file formats (audio transcription, video frames)
- Spaced repetition algorithm for better learning
- User authentication and personal flashcard collections
- Export flashcards to Anki or other formats
- Collaborative flashcard sets
- Multi-page PDF image extraction
- Batch image processing

## License

This project is open source and available for educational purposes.

