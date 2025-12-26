#!/bin/bash
# Don't use set -e here - we want to handle errors gracefully
set -o pipefail

# Debug: Print environment variables (force output to stderr so it shows in logs)
echo "[DEBUG] PORT environment variable: ${PORT:-not set, using 8000}" >&2
echo "[DEBUG] All environment variables:" >&2
env | grep -E "(PORT|DJANGO|PYTHON)" | head -20 >&2 || true

echo "[INFO] Running database migrations..." >&2
python manage.py migrate --noinput || {
    echo "[WARNING] Migrations failed, continuing anyway..." >&2
}

# Railway sets PORT dynamically - we MUST use it
# If PORT is not set, something is wrong, but we'll default to 8000 for safety
LISTEN_PORT=${PORT:-8000}

# Critical: Railway requires binding to $PORT
if [ -z "$PORT" ]; then
    echo "[WARNING] PORT environment variable not set! Railway may not route traffic correctly." >&2
    echo "[WARNING] Defaulting to port 8000, but this may cause 502 errors." >&2
else
    echo "[INFO] Using Railway PORT=${PORT}" >&2
fi

echo "[INFO] Starting gunicorn server on 0.0.0.0:${LISTEN_PORT}..." >&2

# Start gunicorn - Railway will route traffic to this port
exec gunicorn flashcard_app.wsgi:application \
    --bind 0.0.0.0:${LISTEN_PORT} \
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

