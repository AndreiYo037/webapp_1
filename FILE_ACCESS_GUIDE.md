# How to Access Flashcard App Files

## Project Location
**Main Directory:** `C:\Users\alohp`

## Quick Access Methods

### 1. **Open in VS Code / Cursor (Recommended)**
```powershell
cd C:\Users\alohp
code .
```
Or simply:
- Open VS Code/Cursor
- File → Open Folder
- Navigate to `C:\Users\alohp`

### 2. **Open in Windows File Explorer**
- Press `Win + E` to open File Explorer
- Navigate to: `C:\Users\alohp`
- Or run: `explorer C:\Users\alohp` in terminal

### 3. **Access via Terminal/Command Line**
```powershell
cd C:\Users\alohp
dir                    # List files in current directory
dir flashcard_app      # List Django project files
dir flashcards         # List app files
```

## File Structure Overview

### Root Level Files
- `manage.py` - Django management commands
- `db.sqlite3` - Database file
- `README.md` - Project documentation
- `requirements.txt` - Dependencies

### Django Project (`flashcard_app/`)
- `settings.py` - Main configuration
- `urls.py` - URL routing
- `wsgi.py` / `asgi.py` - Server configuration

### Main App (`flashcards/`)
- `models.py` - Database models
- `views.py` - View functions (business logic)
- `urls.py` - App URL routes
- `file_processor.py` - File processing utilities
- `admin.py` - Admin interface config
- `templates/flashcards/` - HTML templates

## Common File Operations

### View a File
```powershell
# In PowerShell
Get-Content manage.py
Get-Content flashcard_app\settings.py
Get-Content flashcards\views.py
```

### Edit a File
- Double-click in File Explorer (opens with default editor)
- Right-click → Open with → VS Code/Cursor
- Or open in your code editor

### Search Files
```powershell
# Find all Python files
Get-ChildItem -Recurse -Filter *.py

# Find specific file
Get-ChildItem -Recurse -Filter settings.py
```

## Recommended Workflow

1. **Open the project folder in VS Code/Cursor** (best for editing)
2. **Use the integrated terminal** for running commands
3. **Use File Explorer** for quick file browsing

## Quick Commands

```powershell
# Navigate to project
cd C:\Users\alohp

# List all Python files
Get-ChildItem -Recurse -Filter *.py | Select-Object FullName

# List all HTML templates
Get-ChildItem -Recurse -Filter *.html | Select-Object FullName

# Open specific file in default editor
Invoke-Item manage.py
Invoke-Item flashcard_app\settings.py
```

