# Migration to add image fields to Flashcard model
# Note: cropped_image already exists from migration 0003
# This migration is a no-op for fresh databases, but ensures consistency

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('flashcards', '0006_fix_flashcardset_file_reference'),
    ]

    operations = [
        # Note: cropped_image field already exists from migration 0003_flashcard_cropped_image
        # source_image field already exists from migration 0002_flashcard_source_image
        # This migration is intentionally empty to maintain migration sequence
        # For fresh databases, all fields will be created by previous migrations
    ]

