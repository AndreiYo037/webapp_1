# Migration to fix source_image foreign key from UploadedFile to FileUpload

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('flashcards', '0007_add_image_fields_to_flashcard'),
    ]

    operations = [
        # Remove the old source_image field that references uploadedfile
        migrations.RemoveField(
            model_name='flashcard',
            name='source_image',
        ),
        # Add the new source_image field that references fileupload
        migrations.AddField(
            model_name='flashcard',
            name='source_image',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='flashcards', to='flashcards.fileupload'),
        ),
    ]

