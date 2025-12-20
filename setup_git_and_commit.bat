@echo off
echo ========================================
echo Git Setup and Commit Script
echo ========================================
echo.

echo Step 1: Setting up Git identity...
echo Please enter your name (or press Enter to skip):
set /p GIT_NAME="Your Name: "

echo Please enter your email (or press Enter to skip):
set /p GIT_EMAIL="Your Email: "

if not "%GIT_NAME%"=="" (
    git config --global user.name "%GIT_NAME%"
    echo Git user.name set to: %GIT_NAME%
)

if not "%GIT_EMAIL%"=="" (
    git config --global user.email "%GIT_EMAIL%"
    echo Git user.email set to: %GIT_EMAIL%
)

echo.
echo Step 2: Committing your code...
git commit -m "Initial commit: Flashcard app with Groq AI integration"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo SUCCESS! Your code is committed!
    echo ========================================
    echo.
    echo Next steps:
    echo 1. Create a repository on GitHub: https://github.com/new
    echo 2. Then run: git remote add origin https://github.com/YOUR_USERNAME/flashcard-app.git
    echo 3. Then run: git push -u origin main
    echo.
    echo See PUSH_TO_GITHUB.md for detailed instructions!
) else (
    echo.
    echo Error committing. Please check the error message above.
)

pause

