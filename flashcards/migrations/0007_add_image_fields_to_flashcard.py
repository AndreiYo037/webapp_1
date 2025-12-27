# Migration to add image fields to Flashcard model

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('flashcards', '0006_fix_flashcardset_file_reference'),
    ]

    operations = [
        # Add cropped_image field (source_image already exists from migration 0002)
        migrations.AddField(
            model_name='flashcard',
            name='cropped_image',
            field=models.ImageField(blank=True, null=True, upload_to='flashcard_crops/'),
        ),
        # Note: source_image field already exists from migration 0002_flashcard_source_image
        # It references 'flashcards.uploadedfile', but we now use 'flashcards.fileupload'
        # For fresh databases, this is fine as migrations run sequentially
    ]

