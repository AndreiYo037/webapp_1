@echo off
echo ========================================
echo Push to GitHub - Flashcard App
echo ========================================
echo.

echo Your code is committed and ready to push!
echo.

echo IMPORTANT: Create a GitHub repository FIRST!
echo Go to: https://github.com/new
echo.
echo After creating the repo, enter your GitHub username:
set /p GITHUB_USER="GitHub Username: "

if "%GITHUB_USER%"=="" (
    echo Error: GitHub username is required!
    pause
    exit /b 1
)

echo.
echo Enter repository name (or press Enter for 'flashcard-app'):
set /p REPO_NAME="Repository Name: "

if "%REPO_NAME%"=="" set REPO_NAME=flashcard-app

echo.
echo Setting up remote and pushing...
echo.

cd /d C:\Users\alohp

REM Remove existing remote if any
git remote remove origin 2>nul

REM Add new remote
git remote add origin https://github.com/%GITHUB_USER%/%REPO_NAME%.git

REM Rename branch to main
git branch -M main

echo.
echo ========================================
echo Ready to push!
echo ========================================
echo.
echo Repository: https://github.com/%GITHUB_USER%/%REPO_NAME%.git
echo.
echo Pushing to GitHub...
echo (You may be asked for GitHub credentials)
echo.

git push -u origin main

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo SUCCESS! Your code is on GitHub!
    echo ========================================
    echo.
    echo Repository URL: https://github.com/%GITHUB_USER%/%REPO_NAME%
    echo.
    echo Next step: Deploy to Railway!
    echo Go to: https://railway.app
    echo.
) else (
    echo.
    echo ========================================
    echo Push failed!
    echo ========================================
    echo.
    echo Common issues:
    echo 1. Repository doesn't exist - Create it at https://github.com/new
    echo 2. Authentication failed - Use Personal Access Token
    echo    Get one at: https://github.com/settings/tokens
    echo 3. Wrong username/repo name - Check and try again
    echo.
    echo See PUSH_NOW.md for detailed help!
    echo.
)

pause


