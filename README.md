# Flashcard App

A Django-based flashcard application with freemium model, email verification, and subscription management.

## Features

- 📚 File upload and automatic flashcard generation (.txt, .pdf, .docx, .md)
- 👤 User authentication with email verification
- 🔐 Password reset functionality
- 💳 Freemium model (3 free generations, then premium required)
- 📧 Email notifications
- 🎯 Test taking with scoring
- 💰 Subscription management (cancel, renew)
- 🔔 Payment webhook support

## Railway Deployment

This app is configured for deployment on Railway.

### Environment Variables

Set these in your Railway project settings:

**Required:**
- `SECRET_KEY` - Django secret key (generate with: `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`)
- `DEBUG` - Set to `False` for production
- `ALLOWED_HOSTS` - Comma-separated list of allowed hosts (e.g., `your-app.railway.app,yourdomain.com`)

**Database (Railway auto-provisions PostgreSQL):**
- `DATABASE_URL` - Automatically set by Railway when you add a PostgreSQL service

**Email (Optional but recommended):**
- `EMAIL_HOST` - SMTP server (e.g., `smtp.sendgrid.net`)
- `EMAIL_PORT` - SMTP port (usually `587`)
- `EMAIL_USE_TLS` - Set to `True`
- `EMAIL_HOST_USER` - Your email username/API key
- `EMAIL_HOST_PASSWORD` - Your email password/API key
- `DEFAULT_FROM_EMAIL` - Sender email address

**Payment Gateway (Optional):**
- `STRIPE_PUBLIC_KEY` - Stripe public key
- `STRIPE_SECRET_KEY` - Stripe secret key
- `STRIPE_WEBHOOK_SECRET` - Stripe webhook secret

### Deployment Steps

1. **Push to Git:**
   ```bash
   git add .
   git commit -m "Initial commit"
   git push origin main
   ```

2. **Deploy on Railway:**
   - Connect your GitHub repository
   - Railway will automatically detect the Django app
   - Add a PostgreSQL service
   - Set environment variables
   - Deploy!

3. **Run Migrations:**
   Railway will automatically run migrations via the Procfile.

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run server
python manage.py runserver
```

## Project Structure

```
flashcard_app/
├── manage.py
├── Procfile              # Railway deployment config
├── requirements.txt      # Python dependencies
├── runtime.txt          # Python version
├── flashcard_app/       # Django project
│   ├── settings.py
│   ├── urls.py
│   └── ...
└── flashcards/          # Main app
    ├── models.py
    ├── views.py
    ├── templates/
    └── ...
```

## License

MIT

