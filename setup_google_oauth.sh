#!/bin/bash
# Script to set up Google OAuth automatically if environment variables are set
# This runs after migrations to ensure the database is ready

echo "[INFO] Checking for Google OAuth credentials..."

if [ -n "$GOOGLE_OAUTH_CLIENT_ID" ] && [ -n "$GOOGLE_OAUTH_CLIENT_SECRET" ]; then
    echo "[INFO] Google OAuth credentials found, setting up SocialApplication..."
    python manage.py setup_google_oauth
else
    echo "[INFO] Google OAuth credentials not found in environment variables."
    echo "[INFO] You can set up Google OAuth manually via Django Admin at /admin/socialaccount/socialapp/"
    echo "[INFO] Or set GOOGLE_OAUTH_CLIENT_ID and GOOGLE_OAUTH_CLIENT_SECRET environment variables."
fi

