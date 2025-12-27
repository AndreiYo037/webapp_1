"""
Setup script to help configure the Django project for flashcards app.
Run this from your main Django project directory.
"""
import os
import sys

def check_django_project():
    """Check if we're in a Django project"""
    if not os.path.exists('manage.py'):
        print("❌ Error: manage.py not found. Please run this script from your Django project root.")
        return False
    return True

def update_settings():
    """Create or update settings.py with required configuration"""
    settings_file = None
    
    # Try to find settings.py
    for root, dirs, files in os.walk('.'):
        if 'settings.py' in files:
            settings_path = os.path.join(root, 'settings.py')
            print(f"✓ Found settings.py at: {settings_path}")
            settings_file = settings_path
            break
    
    if not settings_file:
        print("⚠️  Warning: settings.py not found. You'll need to manually configure settings.")
        return False
    
    # Read current settings
    with open(settings_file, 'r') as f:
        content = f.read()
    
    # Check if flashcards is already in INSTALLED_APPS
    if 'flashcards' in content:
        print("✓ Flashcards app already in INSTALLED_APPS")
    else:
        print("⚠️  Please add 'flashcards.apps.FlashcardsConfig' to INSTALLED_APPS in settings.py")
        print("   Example:")
        print("   INSTALLED_APPS = [")
        print("       # ... other apps")
        print("       'flashcards.apps.FlashcardsConfig',")
        print("   ]")
    
    # Check for email configuration
    if 'EMAIL_BACKEND' in content:
        print("✓ Email configuration found")
    else:
        print("⚠️  Email configuration not found. Add this to settings.py for development:")
        print("   EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'")
    
    # Check for media configuration
    if 'MEDIA_ROOT' in content:
        print("✓ Media files configuration found")
    else:
        print("⚠️  Add media configuration to settings.py:")
        print("   MEDIA_URL = '/media/'")
        print("   MEDIA_ROOT = os.path.join(BASE_DIR, 'media')")
    
    return True

def check_urls():
    """Check if flashcards URLs are included"""
    urls_file = None
    
    for root, dirs, files in os.walk('.'):
        if 'urls.py' in files and root != './flashcards':
            urls_path = os.path.join(root, 'urls.py')
            with open(urls_path, 'r') as f:
                content = f.read()
                if 'ROOT_URLCONF' in content or 'urlpatterns' in content:
                    urls_file = urls_path
                    break
    
    if urls_file:
        with open(urls_file, 'r') as f:
            content = f.read()
        if 'flashcards' in content:
            print(f"✓ Flashcards URLs already included in {urls_file}")
        else:
            print(f"⚠️  Please add flashcards URLs to {urls_file}:")
            print("   from django.urls import path, include")
            print("   urlpatterns = [")
            print("       # ... other patterns")
            print("       path('flashcards/', include('flashcards.urls')),")
            print("   ]")
    else:
        print("⚠️  Could not find main urls.py. Please manually include flashcards URLs.")

def main():
    print("=" * 60)
    print("Flashcard App Setup Script")
    print("=" * 60)
    print()
    
    if not check_django_project():
        sys.exit(1)
    
    print("✓ Django project detected")
    print()
    
    update_settings()
    print()
    check_urls()
    print()
    
    print("=" * 60)
    print("Next Steps:")
    print("=" * 60)
    print("1. Install dependencies: pip install -r flashcards/requirements.txt")
    print("2. Add 'flashcards.apps.FlashcardsConfig' to INSTALLED_APPS")
    print("3. Include flashcards URLs in your main urls.py")
    print("4. Configure email settings (see SETTINGS_GUIDE.md)")
    print("5. Run: python manage.py makemigrations")
    print("6. Run: python manage.py migrate")
    print("7. Create superuser: python manage.py createsuperuser")
    print("8. Run server: python manage.py runserver")
    print()

if __name__ == '__main__':
    main()

