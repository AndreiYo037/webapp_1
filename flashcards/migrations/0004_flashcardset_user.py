# Generated migration for adding user field to FlashcardSet

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('flashcards', '0003_flashcard_cropped_image'),
    ]

    operations = [
        migrations.AddField(
            model_name='flashcardset',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='flashcard_sets', to=settings.AUTH_USER_MODEL),
        ),
    ]

