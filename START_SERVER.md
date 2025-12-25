# 🚀 How to Start Your Flashcard App Server

## Quick Start

### Option 1: Development Server (Recommended for Testing)

```bash
python manage.py runserver
```

Then open: **http://127.0.0.1:8000** in your browser

### Option 2: Production Server (Gunicorn)

```bash
gunicorn flashcard_app.wsgi --bind 0.0.0.0:8000
```

Or use the config file:
```bash
gunicorn -c gunicorn_config.py flashcard_app.wsgi
```

### Option 3: Using the Batch Script (Windows)

```bash
start_production.bat
```

## Server Status

✅ **Server is running!**

Access your app at:
- **Local**: http://127.0.0.1:8000
- **Network**: http://your-ip:8000

## What to Do Next

1. **Open your browser** and go to http://127.0.0.1:8000
2. **Upload a file** (PDF, DOC, TXT, etc.)
3. **See AI-generated flashcards** powered by Groq!

## Stop the Server

Press `Ctrl+C` in the terminal where the server is running.

## Troubleshooting

### Port 8000 already in use?
```bash
# Use a different port
python manage.py runserver 8080
```

### "Module not found" error?
```bash
# Install dependencies
pip install -r requirements.txt
```

### Database errors?
```bash
# Run migrations
python manage.py migrate
```

## Features Available

✅ File upload (PDF, DOC, DOCX, XLS, XLSX, TXT)
✅ AI-powered flashcard generation (Groq)
✅ Interactive flashcard viewing
✅ Practice tests
✅ Results tracking

Enjoy your flashcard app! 🎉


