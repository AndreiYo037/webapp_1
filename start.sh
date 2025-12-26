#!/bin/bash
set -e

# Debug: Print environment variables
echo "[DEBUG] PORT environment variable: ${PORT:-not set, using 8000}"
echo "[DEBUG] DJANGO_SETTINGS_MODULE: ${DJANGO_SETTINGS_MODULE:-not set}"
echo "[DEBUG] PYTHONPATH: ${PYTHONPATH:-not set}"

echo "[INFO] Running database migrations..."
python manage.py migrate --noinput || echo "[WARNING] Migrations failed, continuing anyway..."

# Use PORT if set, otherwise default to 8000
LISTEN_PORT=${PORT:-8000}
echo "[INFO] Starting gunicorn server on port ${LISTEN_PORT}..."

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
    --capture-output

