"""
Management command to set up Google OAuth credentials from environment variables.
Run this after setting GOOGLE_OAUTH_CLIENT_ID and GOOGLE_OAUTH_CLIENT_SECRET.
"""
from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp
from django.conf import settings
import os


class Command(BaseCommand):
    help = 'Set up Google OAuth SocialApplication from environment variables'

    def handle(self, *args, **options):
        client_id = os.getenv('GOOGLE_OAUTH_CLIENT_ID', '')
        client_secret = os.getenv('GOOGLE_OAUTH_CLIENT_SECRET', '')
        
        if not client_id or not client_secret:
            self.stdout.write(
                self.style.WARNING(
                    'GOOGLE_OAUTH_CLIENT_ID and GOOGLE_OAUTH_CLIENT_SECRET must be set in environment variables'
                )
            )
            return
        
        # Get or create the default site
        site = Site.objects.get_current()
        
        # Get or create the Google social app
        social_app, created = SocialApp.objects.get_or_create(
            provider='google',
            defaults={
                'name': 'Google',
                'client_id': client_id,
                'secret': client_secret,
            }
        )
        
        if not created:
            # Update existing app
            social_app.client_id = client_id
            social_app.secret = client_secret
            social_app.save()
            self.stdout.write(self.style.SUCCESS('Updated existing Google OAuth app'))
        else:
            self.stdout.write(self.style.SUCCESS('Created new Google OAuth app'))
        
        # Add site to the app if not already added
        if site not in social_app.sites.all():
            social_app.sites.add(site)
            self.stdout.write(self.style.SUCCESS(f'Added site {site.domain} to Google OAuth app'))
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Google OAuth is configured. Client ID: {client_id[:10]}...'
            )
        )

