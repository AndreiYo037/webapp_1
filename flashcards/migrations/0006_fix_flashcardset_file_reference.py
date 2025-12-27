# Migration to fix FlashcardSet file reference
# Make old 'file' field nullable and make 'file_upload' required

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('flashcards', '0005_add_user_models'),
    ]

    operations = [
        # Make the old 'file' field nullable (for backward compatibility)
        migrations.AlterField(
            model_name='flashcardset',
            name='file',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='flashcard_sets_old', to='flashcards.uploadedfile'),
        ),
        # Make 'file_upload' required (NOT NULL) since it's the primary field now
        migrations.AlterField(
            model_name='flashcardset',
            name='file_upload',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='flashcard_sets', to='flashcards.fileupload'),
        ),
    ]

