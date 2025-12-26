#!/bin/bash
set -e  # Exit on error

echo "=========================================="
echo "[STARTUP] Flashcard App Starting"
echo "=========================================="

# Debug: Print PORT environment variable
echo "[DEBUG] PORT environment variable: ${PORT:-NOT SET}"
if [ -z "$PORT" ]; then
    echo "[ERROR] PORT environment variable is NOT SET!"
    echo "[ERROR] Railway requires your app to listen on \$PORT"
    echo "[ERROR] This will cause 502 Bad Gateway errors"
    echo "[ERROR] Attempting to use port 8000 as fallback..."
    export PORT=8000
else
    echo "[SUCCESS] PORT is set to: ${PORT}"
fi

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

