# Settings Configuration Guide

This guide explains how to configure your Django project settings for the Flashcard App.

## Email Configuration

The app requires email configuration to send verification emails, password resets, and subscription notifications.

### Option 1: Gmail SMTP (Development)

Add to your `settings.py`:

```python
# Email Configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-password'  # Use App Password, not regular password
DEFAULT_FROM_EMAIL = 'your-email@gmail.com'
SERVER_EMAIL = 'your-email@gmail.com'
```

**Note:** For Gmail, you need to:
1. Enable 2-factor authentication
2. Generate an App Password: https://myaccount.google.com/apppasswords

### Option 2: SendGrid (Production Recommended)

```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.sendgrid.net'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'apikey'
EMAIL_HOST_PASSWORD = 'your-sendgrid-api-key'
DEFAULT_FROM_EMAIL = 'noreply@yourdomain.com'
SERVER_EMAIL = 'noreply@yourdomain.com'
```

### Option 3: Console Backend (Development/Testing)

For development, you can use the console backend to see emails in the terminal:

```python
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

### Option 4: File Backend (Development)

Emails are saved as files:

```python
EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
EMAIL_FILE_PATH = '/tmp/app-messages'
```

## Payment Gateway Configuration

### Stripe Integration

Add to your `settings.py`:

```python
# Stripe Configuration
STRIPE_PUBLIC_KEY = 'your-stripe-public-key'
STRIPE_SECRET_KEY = 'your-stripe-secret-key'
STRIPE_WEBHOOK_SECRET = 'your-webhook-secret'  # For webhook verification
```

Update `views.py` in the `payment_webhook` function to verify webhook signatures:

```python
import stripe

@csrf_exempt
@require_http_methods(["POST"])
def payment_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
        # Process event...
    except ValueError:
        return JsonResponse({'error': 'Invalid payload'}, status=400)
    except stripe.error.SignatureVerificationError:
        return JsonResponse({'error': 'Invalid signature'}, status=400)
```

## Required Settings

Make sure these are in your main project's `settings.py`:

```python
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'flashcards.apps.FlashcardsConfig',  # Important: Use the config class
]

# URL Configuration
ROOT_URLCONF = 'yourproject.urls'

# Include flashcards URLs in your main urls.py:
# urlpatterns = [
#     path('flashcards/', include('flashcards.urls')),
# ]

# Media files (for file uploads)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Templates
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],  # If you have a global templates dir
        'APP_DIRS': True,  # This allows Django to find templates in app directories
        # ...
    },
]
```

## Security Settings (Production)

```python
# Security settings for production
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
```

## Database

The app uses Django's default database. For production, use PostgreSQL:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'flashcards_db',
        'USER': 'your_user',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

## Running Migrations

After configuration, run:

```bash
python manage.py makemigrations
python manage.py migrate
```

## Testing Email

To test email functionality in development:

```python
# settings.py
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

This will print emails to the console instead of sending them.

