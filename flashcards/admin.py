from django.contrib import admin
from .models import UploadedFile, FlashcardSet, Flashcard


@admin.register(UploadedFile)
class UploadedFileAdmin(admin.ModelAdmin):
    list_display = ['filename', 'file_type', 'user', 'uploaded_at', 'processed']
    list_filter = ['file_type', 'processed', 'uploaded_at']
    search_fields = ['filename']


@admin.register(FlashcardSet)
class FlashcardSetAdmin(admin.ModelAdmin):
    list_display = ['title', 'file', 'user', 'created_at']
    list_filter = ['created_at', 'user']
    search_fields = ['title']
    list_select_related = ['user', 'file']


@admin.register(Flashcard)
class FlashcardAdmin(admin.ModelAdmin):
    list_display = ['question', 'flashcard_set', 'source_image', 'created_at']
    list_filter = ['flashcard_set', 'created_at', 'source_image']
    search_fields = ['question', 'answer']
    fields = ['flashcard_set', 'question', 'answer', 'source_image', 'created_at']
    readonly_fields = ['created_at']



