#!/bin/bash
set -e

echo "[INFO] Running database migrations..."
python manage.py migrate --noinput

echo "[INFO] Starting gunicorn server on port ${PORT:-8000}..."
exec gunicorn flashcard_app.wsgi:application \
    --bind 0.0.0.0:${PORT:-8000} \
    --workers 2 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -

