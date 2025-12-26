"""
Django settings for flashcard_app project.
"""

from pathlib import Path
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-dev-key-change-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

# ALLOWED_HOSTS configuration
# This is critical for deployment - must include your domain!
allowed_hosts_env = os.getenv('ALLOWED_HOSTS', '').strip()
allow_all_hosts = os.getenv('ALLOW_ALL_HOSTS', 'False').lower() == 'true'

if allow_all_hosts:
    # Allow all hosts (useful for testing/deployment)
    ALLOWED_HOSTS = ['*']
elif allowed_hosts_env:
    # Split by comma and strip whitespace, filter out empty strings
    ALLOWED_HOSTS = [host.strip() for host in allowed_hosts_env.split(',') if host.strip()]
    # If '*' is in the list, allow all hosts
    if '*' in ALLOWED_HOSTS:
        ALLOWED_HOSTS = ['*']
else:
    # Default to localhost for development
    # In production, this will cause 400 errors if domain not set!
    ALLOWED_HOSTS = ['localhost', '127.0.0.1']
    
    # If DEBUG is False and we're in production, warn but allow all for safety
    if not DEBUG:
        # In production without ALLOWED_HOSTS set, allow all to prevent 400 errors
        # This is less secure but better than a broken app
        ALLOWED_HOSTS = ['*']
        import warnings
        warnings.warn(
            "ALLOWED_HOSTS not set in production! Allowing all hosts. "
            "Set ALLOWED_HOSTS environment variable for security.",
            UserWarning
        )


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',  # Required for allauth
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'flashcards',
]

SITE_ID = 1

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # For static files in production
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'allauth.account.middleware.AccountMiddleware',  # Required for django-allauth
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Authentication backends
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

ROOT_URLCONF = 'flashcard_app.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'flashcards.context_processors.llm_info',  # Add LLM info to all templates
            ],
        },
    },
]

WSGI_APPLICATION = 'flashcard_app.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static'] if (BASE_DIR / 'static').exists() else []

# WhiteNoise configuration for static files
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media files
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Security settings for production
# CSRF trusted origins - important for deployment!
# Set this to your actual domain
csrf_trusted_origins_env = os.getenv('CSRF_TRUSTED_ORIGINS', '')
if csrf_trusted_origins_env:
    CSRF_TRUSTED_ORIGINS = [origin.strip() for origin in csrf_trusted_origins_env.split(',') if origin.strip()]
else:
    # Auto-detect from ALLOWED_HOSTS if not set
    if ALLOWED_HOSTS == ['*']:
        # If allowing all hosts, trust all HTTPS origins
        CSRF_TRUSTED_ORIGINS = ['https://*']
    else:
        # Build from ALLOWED_HOSTS
        CSRF_TRUSTED_ORIGINS = []
        for host in ALLOWED_HOSTS:
            if host and host != '*':
                # Add both http and https for flexibility
                CSRF_TRUSTED_ORIGINS.append(f"https://{host}")
                CSRF_TRUSTED_ORIGINS.append(f"http://{host}")

if not DEBUG:
    # Security settings for production
    # Note: Some platforms (Railway, Render) handle SSL at the proxy level
    SECURE_SSL_REDIRECT = os.getenv('SECURE_SSL_REDIRECT', 'False').lower() == 'true'
    
    # Cookie security - only enable if using HTTPS
    # Disable for now to avoid issues with platforms that use HTTP internally
    SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
    CSRF_COOKIE_SECURE = os.getenv('CSRF_COOKIE_SECURE', 'False').lower() == 'true'
    
    SECURE_HSTS_SECONDS = int(os.getenv('SECURE_HSTS_SECONDS', '31536000'))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# LLM Configuration
# Provider options: 'groq' (free, cloud - recommended for deployment), 'gemini' (free, cloud), 'ollama' (free, local - NOT for cloud deployment), 'none' (rule-based)
# Default to Groq (cloud-based, works on Railway/Render/etc!)
LLM_PROVIDER = os.getenv('LLM_PROVIDER', 'groq').lower()

# Force cloud LLM in production if Ollama is configured
if not DEBUG and LLM_PROVIDER == 'ollama':
    import warnings
    warnings.warn(
        "Ollama is configured but won't work on cloud platforms (Railway, Render, etc.). "
        "Auto-switching to Groq. Set LLM_PROVIDER=groq or LLM_PROVIDER=gemini explicitly.",
        UserWarning
    )
    # Auto-switch to Groq in production
    LLM_PROVIDER = 'groq'

# Groq Configuration (Free, Cloud-Based - Works on all platforms!)
GROQ_API_KEY = os.getenv('GROQ_API_KEY', '')
GROQ_MODEL = os.getenv('GROQ_MODEL', 'llama-3.3-70b-versatile')  # Options: llama-3.3-70b-versatile, mixtral-8x7b-32768, gemma2-9b-it
GROQ_VISION_MODEL = os.getenv('GROQ_VISION_MODEL', 'llava-3.1-70b-versatile')  # For image/diagram understanding

# Gemini Configuration (Free, Cloud-Based - Google AI)
# Note: Vision analysis now uses Groq by default, but Gemini is still available for text generation
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-pro')  # Options: gemini-pro (works with deprecated API), gemini-1.5-pro (if available)

# Ollama Configuration (Free & Local - Only works if Ollama is installed)
OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'mistral')  # Options: mistral, llama3, gemma, phi, qwen

USE_LLM = os.getenv('USE_LLM', 'true').lower() == 'true'  # Set to 'false' to use rule-based generation

# Flashcard Generation Settings
DEFAULT_FLASHCARDS_COUNT = int(os.getenv('DEFAULT_FLASHCARDS_COUNT', '20'))  # Default number of flashcards to generate

# Visual Region Matching Settings
# Set to 'false' to disable visual region detection and matching (uses standard image extraction instead)
# This can help if you experience memory issues with large documents
ENABLE_VISUAL_REGIONS = os.getenv('ENABLE_VISUAL_REGIONS', 'true').lower() == 'true'

# Django Allauth Configuration
ACCOUNT_LOGIN_METHODS = {'email'}  # Use email for authentication
ACCOUNT_SIGNUP_FIELDS = ['email*', 'password1*', 'password2*']  # Email is required, username not required
ACCOUNT_EMAIL_VERIFICATION = 'none'  # Set to 'mandatory' if you want email verification
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

# Google OAuth Settings
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        },
        'APP': {
            'client_id': os.getenv('GOOGLE_OAUTH_CLIENT_ID', ''),
            'secret': os.getenv('GOOGLE_OAUTH_CLIENT_SECRET', ''),
            'key': ''
        }
    }
}


