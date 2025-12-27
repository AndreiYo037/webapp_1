# Migration to add image fields to Flashcard model

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('flashcards', '0006_fix_flashcardset_file_reference'),
    ]

    operations = [
        # Add source_image field (already exists in migration 0002, but ensure it's there)
        # Add cropped_image field
        migrations.AddField(
            model_name='flashcard',
            name='cropped_image',
            field=models.ImageField(blank=True, null=True, upload_to='flashcard_crops/'),
        ),
        # Ensure source_image field exists (it should from migration 0002)
        # If it doesn't exist, this will add it
        migrations.AddField(
            model_name='flashcard',
            name='source_image',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='flashcards', to='flashcards.fileupload'),
        ),
    ]

