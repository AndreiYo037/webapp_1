#!/bin/bash
set -e  # Exit on error - we want to fail loudly if PORT isn't set

# Force output to stdout/stderr (don't buffer)
exec > >(tee -a /proc/1/fd/1) 2>&1

echo "=========================================="
echo "[STARTUP] Flashcard App Starting"
echo "=========================================="

# Debug: Print environment variables
echo "[DEBUG] PORT environment variable: ${PORT:-NOT SET - THIS WILL CAUSE 502 ERRORS}"
echo "[DEBUG] Checking environment..."
env | grep -E "^PORT=" || echo "[ERROR] PORT environment variable is NOT SET!"

# CRITICAL: Railway REQUIRES PORT to be set
if [ -z "$PORT" ]; then
    echo "[FATAL ERROR] PORT environment variable is not set!"
    echo "[FATAL ERROR] Railway requires your app to listen on \$PORT"
    echo "[FATAL ERROR] This will cause 502 Bad Gateway errors"
    echo "[FATAL ERROR] Exiting..."
    exit 1
fi

echo "[SUCCESS] PORT is set to: ${PORT}"
echo "[INFO] Running database migrations..."
python manage.py migrate --noinput || {
    echo "[WARNING] Migrations failed, continuing anyway..."
}

echo "[INFO] Starting gunicorn server on 0.0.0.0:${PORT}..."
echo "=========================================="

# Start gunicorn - MUST use $PORT (no default, fail if not set)
exec gunicorn flashcard_app.wsgi:application \
    --bind 0.0.0.0:${PORT} \
    --workers 2 \
    --timeout 120 \
    --keep-alive 5 \
    --max-requests 1000 \
    --max-requests-jitter 50 \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    --capture-output \
    --enable-stdio-inheritance

