#!/bin/bash
set -e

# CRITICAL: Force unbuffered output so logs show immediately
export PYTHONUNBUFFERED=1

# Print startup banner - this MUST appear in logs
echo "=========================================="
echo "[STARTUP] Flashcard App Starting"
echo "=========================================="
echo "[CRITICAL] Checking PORT environment variable..."

# CRITICAL: Railway MUST provide PORT - check it exists
if [ -z "$PORT" ]; then
    echo "[FATAL] PORT environment variable is NOT SET!"
    echo "[FATAL] Railway requires your app to listen on \$PORT"
    echo "[FATAL] This WILL cause 502 Bad Gateway errors"
    echo "[FATAL] Exiting to prevent deployment with wrong port..."
    exit 1
fi

echo "[SUCCESS] PORT is set to: ${PORT}"
echo "[INFO] This is the port Railway expects the app to listen on"

echo "[INFO] Running database migrations..."
python manage.py migrate --noinput || {
    echo "[WARNING] Migrations failed, continuing anyway..."
}

# Set up Google OAuth if credentials are provided via environment variables
if [ -n "$GOOGLE_OAUTH_CLIENT_ID" ] && [ -n "$GOOGLE_OAUTH_CLIENT_SECRET" ]; then
    echo "[INFO] Google OAuth credentials found, setting up SocialApplication..."
    python manage.py setup_google_oauth || {
        echo "[WARNING] Failed to set up Google OAuth automatically. You can set it up manually via Django Admin."
    }
else
    echo "[INFO] Google OAuth credentials not found. Set up manually via Django Admin at /admin/socialaccount/socialapp/"
    echo "[INFO] See GOOGLE_OAUTH_SETUP.md for detailed instructions."
fi

echo "[INFO] Starting gunicorn server..."
echo "[INFO] Binding to: 0.0.0.0:${PORT}"
echo "=========================================="

# CRITICAL: Use $PORT directly - NO fallback, NO default
# Railway's proxy routes to this exact port
exec gunicorn flashcard_app.wsgi:application \
    --bind "0.0.0.0:${PORT}" \
    --workers 2 \
    --timeout 600 \
    --graceful-timeout 30 \
    --keep-alive 5 \
    --max-requests 1000 \
    --max-requests-jitter 50 \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    --capture-output \
    --enable-stdio-inheritance \
    --name flashcard_app

