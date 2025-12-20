# Flashcard Generator Web App

A Django-based web application that automatically generates interactive flashcards from uploaded files. Upload PDFs, Word documents, Excel files, or plain text files, and the app will extract content, create summaries, and generate flashcards for studying.

## Features

- 📄 **Multi-format Support**: Upload TXT, PDF, DOC, DOCX, XLS, XLSX files
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

2. **Set up Groq API (Recommended for AI features):**
   
   For AI-powered flashcard generation, use Groq (free, cloud-based, works everywhere!):
   
   a. Get your free API key from [Groq Console](https://console.groq.com/keys)
   
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

3. **Run database migrations:**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

4. **Create a superuser (optional, for admin access):**
   ```bash
   python manage.py createsuperuser
   ```

5. **Run the development server:**
   ```bash
   python manage.py runserver
   ```

6. **Access the application:**
   - Main app: http://127.0.0.1:8000/
   - Admin panel: http://127.0.0.1:8000/admin/

## Usage

1. **Upload a File:**
   - Go to the home page
   - Click "Upload File" or use the upload area
   - Select a supported file format
   - Wait for processing

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
- **Groq**: Free, cloud-based LLM for AI-powered flashcard generation (works on all platforms!)
- **Ollama**: Alternative free, local LLM option
- **Pillow**: Image processing
- **python-docx**: Word document processing
- **PyPDF2**: PDF text extraction
- **openpyxl**: Excel file processing
- **python-dotenv**: Environment variable management

## How It Works

1. **File Upload**: Files are uploaded and stored in the media directory
2. **Text Extraction**: Content is extracted based on file type
3. **Summarization**: Key sentences are extracted to create summaries
4. **Flashcard Generation**: 
   - **With Groq (if configured)**: Uses cloud-based Groq LLM to generate high-quality, contextually relevant Q&A pairs (free, works on all platforms!)
   - **With Ollama (if running locally)**: Uses local Ollama LLM (for self-hosted deployments)
   - **Without LLM**: Uses rule-based text processing to create flashcards from sentences
   - **Dynamic Count**: Number of flashcards automatically adjusts based on content length
5. **Interactive Study**: Users can flip through flashcards to study questions and answers

## LLM Configuration

The app uses **Groq** (free, cloud-based) by default for enhanced flashcard generation. Configuration options:

- **LLM_PROVIDER**: Set to `groq` (default, recommended), `ollama` (local only), or `none` for rule-based
- **GROQ_API_KEY**: Your Groq API key (get free at https://console.groq.com/keys)
- **GROQ_MODEL**: Model to use (`llama-3.3-70b-versatile` default, `mixtral-8x7b-32768`, `gemma2-9b-it`)
- **OLLAMA_BASE_URL**: Ollama server URL (only if using Ollama: `http://localhost:11434`)
- **OLLAMA_MODEL**: Ollama model (`mistral`, `llama3`, `gemma`, `phi`, or `qwen`)
- **USE_LLM**: Set to `true` to enable LLM, `false` for rule-based generation

The app automatically falls back to rule-based generation if:
- Groq API key is not set or invalid
- Ollama is not running (if using Ollama)
- API request fails
- `USE_LLM` is set to `false`
- `LLM_PROVIDER` is set to `none`

## Future Enhancements

- Support for more free LLM providers (Hugging Face, Google Gemini free tier)
- AI-powered summarization
- Support for more file formats (images with OCR, audio transcription)
- Spaced repetition algorithm for better learning
- User authentication and personal flashcard collections
- Export flashcards to Anki or other formats
- Collaborative flashcard sets

## License

This project is open source and available for educational purposes.

