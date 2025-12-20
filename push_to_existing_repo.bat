@echo off
echo ========================================
echo Push to Existing GitHub Repository
echo ========================================
echo.

echo Repository name: webapp1
echo.

echo Enter your GitHub username:
set /p GITHUB_USER="GitHub Username: "

if "%GITHUB_USER%"=="" (
    echo Error: GitHub username is required!
    pause
    exit /b 1
)

echo.
echo Setting up remote for: https://github.com/%GITHUB_USER%/webapp1.git
echo.

cd /d C:\Users\alohp

REM Remove existing remote if any
git remote remove origin 2>nul

REM Add remote
git remote add origin https://github.com/%GITHUB_USER%/webapp1.git

echo Remote configured!
echo.

REM Check current branch
for /f "tokens=*" %%i in ('git branch --show-current') do set CURRENT_BRANCH=%%i

echo Current branch: %CURRENT_BRANCH%
echo.

REM Ask which branch to push to
echo Which branch to push to? (Press Enter for 'main'):
set /p TARGET_BRANCH="Target branch: "

if "%TARGET_BRANCH%"=="" set TARGET_BRANCH=main

echo.
echo ========================================
echo Ready to push!
echo ========================================
echo.
echo Repository: https://github.com/%GITHUB_USER%/webapp1.git
echo Branch: %TARGET_BRANCH%
echo.
echo Pushing to GitHub...
echo (You may be asked for GitHub credentials)
echo.

REM Rename current branch if needed
if not "%CURRENT_BRANCH%"=="%TARGET_BRANCH%" (
    echo Renaming branch from %CURRENT_BRANCH% to %TARGET_BRANCH%...
    git branch -M %TARGET_BRANCH%
)

REM Push
git push -u origin %TARGET_BRANCH%

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo SUCCESS! Your code is on GitHub!
    echo ========================================
    echo.
    echo Repository URL: https://github.com/%GITHUB_USER%/webapp1
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
    echo 1. Repository doesn't exist - Check the name and username
    echo 2. Authentication failed - Use Personal Access Token
    echo    Get one at: https://github.com/settings/tokens
    echo 3. Branch conflict - Repository might have different content
    echo    Try: git pull origin %TARGET_BRANCH% --allow-unrelated-histories
    echo.
)

pause

