# Final Setup Instructions

## ✅ Completed Automatically

1. **Settings Updated**: `flashcard_app/settings.py` configured with:
   - `flashcards.apps.FlashcardsConfig` in INSTALLED_APPS
   - Email backend (console for development)
   - Media files configuration

2. **Files Copied**: Flashcards app files are in the project

## 🔧 Manual Steps Required

### Step 1: Verify File Structure

The flashcards app should be at: `C:\flashcard_app\flashcards\`

If files are nested incorrectly, manually copy from `C:\flashcards` to `C:\flashcard_app\flashcards\`

### Step 2: Install Dependencies

```powershell
cd C:\flashcard_app
pip install -r flashcards\requirements.txt
```

Or install manually:
```powershell
pip install Django>=4.2 PyPDF2 python-docx stripe
```

### Step 3: Run Migrations

```powershell
cd C:\flashcard_app
python manage.py makemigrations flashcards
python manage.py migrate
```

### Step 4: Create Superuser (Optional)

```powershell
python manage.py createsuperuser
```

### Step 5: Run Server

```powershell
python manage.py runserver
```

Then visit: **http://127.0.0.1:8000/**

## 🧪 Testing Checklist

- [ ] Register a new user at `/register/`
- [ ] Check console for verification email
- [ ] Login at `/login/`
- [ ] Upload a file at `/upload/`
- [ ] View generated flashcards
- [ ] Take a test
- [ ] Check account page at `/account/`
- [ ] Test premium upgrade at `/upgrade/`

## 📝 Notes

- **Email**: Currently configured to print to console (development mode)
- **URLs**: Flashcards are at root path `/` (not `/flashcards/`)
- **Media**: Uploads saved to `media/uploads/` directory

## 🐛 Troubleshooting

**"No module named 'flashcards'"**
- Verify flashcards folder is in `C:\flashcard_app\flashcards\`
- Check `INSTALLED_APPS` in settings.py

**Migration errors**
- Ensure all dependencies installed
- Check Python version (3.8+)

**Template not found**
- Verify `APP_DIRS = True` in TEMPLATES settings
- Check templates are in `flashcards/templates/flashcards/`

## 📚 Documentation

- `QUICK_START.md` - Quick reference
- `SETTINGS_GUIDE.md` - Configuration details
- `FEATURES.md` - Complete feature list

