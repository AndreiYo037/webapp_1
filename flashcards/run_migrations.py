"""
Script to run migrations for the flashcards app.
This can be run from the flashcards app directory or Django project root.
"""
import os
import sys
import subprocess

def find_manage_py():
    """Find manage.py in current or parent directories"""
    current = os.getcwd()
    max_depth = 5
    depth = 0
    
    while depth < max_depth:
        if os.path.exists('manage.py'):
            return os.path.abspath('manage.py')
        parent = os.path.dirname(os.getcwd())
        if parent == os.getcwd():
            break
        os.chdir(parent)
        depth += 1
    
    return None

def run_migrations():
    """Run Django migrations"""
    manage_py = find_manage_py()
    
    if not manage_py:
        print("❌ Error: manage.py not found.")
        print("   Please run this from your Django project root directory.")
        return False
    
    project_dir = os.path.dirname(manage_py)
    os.chdir(project_dir)
    
    print("=" * 60)
    print("Running Django Migrations")
    print("=" * 60)
    print(f"Project directory: {project_dir}")
    print()
    
    # Check if flashcards app exists
    if not os.path.exists('flashcards'):
        print("❌ Error: flashcards app not found in project.")
        print("   Make sure the flashcards app is in your project directory.")
        return False
    
    try:
        print("Step 1: Making migrations...")
        result = subprocess.run(
            [sys.executable, 'manage.py', 'makemigrations', 'flashcards'],
            check=True,
            capture_output=True,
            text=True
        )
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
        
        print("\nStep 2: Applying migrations...")
        result = subprocess.run(
            [sys.executable, 'manage.py', 'migrate'],
            check=True,
            capture_output=True,
            text=True
        )
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
        
        print("\n" + "=" * 60)
        print("✓ Migrations completed successfully!")
        print("=" * 60)
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running migrations:")
        print(e.stdout)
        print(e.stderr)
        return False
    except FileNotFoundError:
        print("❌ Error: Python or Django not found.")
        print("   Make sure Django is installed: pip install -r flashcards/requirements.txt")
        return False

if __name__ == '__main__':
    success = run_migrations()
    sys.exit(0 if success else 1)

