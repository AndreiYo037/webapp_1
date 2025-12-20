@echo off
echo Starting Flashcard App in Production Mode...
echo.

REM Check if .env exists
if not exist .env (
    echo Creating .env file from example...
    copy .env.example .env
    echo.
    echo WARNING: Please edit .env file and set:
    echo   - SECRET_KEY (generate with: python -c "import secrets; print(secrets.token_urlsafe(50))")
    echo   - DEBUG=False
    echo   - ALLOWED_HOSTS
    echo.
    pause
)

REM Collect static files
echo Collecting static files...
python manage.py collectstatic --noinput

REM Run migrations
echo Running database migrations...
python manage.py migrate

echo.
echo Starting Gunicorn server...
echo Access the app at: http://localhost:8000
echo Press Ctrl+C to stop
echo.

gunicorn flashcard_app.wsgi --bind 0.0.0.0:8000

