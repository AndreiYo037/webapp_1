# Quick Start Guide

This guide will help you set up and run the Flashcard App.

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

## Step 1: Install Dependencies

From the flashcards app directory:

```bash
pip install -r requirements.txt
```

Or install individually:
```bash
pip install Django>=4.2 PyPDF2 python-docx stripe
```

## Step 2: Set Up Django Project

### Option A: If you already have a Django project

1. Copy the `flashcards` folder to your Django project directory
2. Add to your `settings.py`:

```python
INSTALLED_APPS = [
    # ... existing apps
    'flashcards.apps.FlashcardsConfig',
]

# Email configuration (for development)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
```

3. Add to your main `urls.py`:

```python
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # ... existing patterns
    path('flashcards/', include('flashcards.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

### Option B: Create a new Django project

```bash
# From parent directory of flashcards folder
django-admin startproject flashcard_project
cd flashcard_project
# Copy flashcards folder here or create symlink
```

Then follow Option A steps.

## Step 3: Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

Or use the provided script:
```bash
python flashcards/run_migrations.py
```

## Step 4: Create Superuser (Optional)

```bash
python manage.py createsuperuser
```

This allows you to access the Django admin panel.

## Step 5: Configure Email (Optional for Development)

For development, emails will print to console. For production, see `SETTINGS_GUIDE.md`.

Add to `settings.py`:
```python
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

## Step 6: Run the Server

```bash
python manage.py runserver
```

Visit: http://127.0.0.1:8000/flashcards/

## Testing the App

1. **Register a new user:**
   - Go to http://127.0.0.1:8000/flashcards/register/
   - Create an account
   - Check console for verification email

2. **Upload a file:**
   - Login
   - Upload a .txt, .pdf, .docx, or .md file
   - View generated flashcards

3. **Test premium features:**
   - After 3 free generations, upgrade to premium
   - Test subscription management

## Troubleshooting

### "No module named 'flashcards'"
- Make sure the flashcards folder is in your Django project directory
- Check that 'flashcards.apps.FlashcardsConfig' is in INSTALLED_APPS

### "Template not found"
- Make sure APP_DIRS = True in TEMPLATES settings
- Templates should be in flashcards/templates/flashcards/

### "Email not sending"
- For development, use console backend (see Step 5)
- For production, configure SMTP (see SETTINGS_GUIDE.md)

### Migration errors
- Make sure all dependencies are installed
- Try: `python manage.py makemigrations flashcards`
- Then: `python manage.py migrate`

## Next Steps

- Configure email for production (see SETTINGS_GUIDE.md)
- Set up payment gateway (Stripe, PayPal, etc.)
- Configure webhook endpoints
- Deploy to production

## Files to Check

- `SETTINGS_GUIDE.md` - Detailed configuration guide
- `FEATURES.md` - Complete feature list
- `requirements.txt` - Python dependencies

