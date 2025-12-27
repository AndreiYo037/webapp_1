"""App configuration for flashcards app"""
from django.apps import AppConfig


class FlashcardsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'flashcards'
    
    def ready(self):
        import flashcards.signals  # noqa: F401

