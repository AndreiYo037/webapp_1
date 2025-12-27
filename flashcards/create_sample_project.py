"""
Script to create a minimal Django project structure for testing the flashcards app.
This creates a basic Django project if one doesn't exist.
"""
import os
import subprocess
import sys

def create_project_structure():
    """Create a minimal Django project structure"""
    project_name = 'flashcard_project'
    
    if os.path.exists('manage.py'):
        print("✓ Django project already exists")
        return True
    
    print("Creating Django project structure...")
    
    try:
        # Check if Django is installed
        subprocess.run([sys.executable, '-m', 'pip', 'show', 'django'], 
                      check=True, capture_output=True)
    except subprocess.CalledProcessError:
        print("❌ Django not installed. Installing...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'django'], check=True)
    
    # Create project in parent directory
    parent_dir = os.path.dirname(os.path.abspath('.'))
    os.chdir(parent_dir)
    
    if not os.path.exists(project_name):
        print(f"Creating Django project: {project_name}")
        subprocess.run([sys.executable, '-m', 'django', 'startproject', project_name], check=True)
        print(f"✓ Project created: {project_name}")
    
    # Move flashcards app into project
    flashcards_path = os.path.join(os.path.dirname(parent_dir), 'flashcards')
    if os.path.exists(flashcards_path) and not os.path.exists(os.path.join(project_name, 'flashcards')):
        import shutil
        shutil.copytree(flashcards_path, os.path.join(project_name, 'flashcards'))
        print("✓ Flashcards app copied to project")
    
    print(f"\n✓ Project structure created in: {os.path.join(parent_dir, project_name)}")
    print(f"  Navigate to: cd {project_name}")
    return True

if __name__ == '__main__':
    create_project_structure()

