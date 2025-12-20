from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class UploadedFile(models.Model):
    """Model to store uploaded files"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    file = models.FileField(upload_to='uploads/')
    filename = models.CharField(max_length=255)
    file_type = models.CharField(max_length=50)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    processed = models.BooleanField(default=False)
    summary = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return self.filename


class FlashcardSet(models.Model):
    """Model to store a set of flashcards generated from a file"""
    file = models.ForeignKey(UploadedFile, on_delete=models.CASCADE, related_name='flashcard_sets')
    title = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title


class Flashcard(models.Model):
    """Model to store individual flashcards"""
    flashcard_set = models.ForeignKey(FlashcardSet, on_delete=models.CASCADE, related_name='flashcards')
    question = models.TextField()
    answer = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['id']
    
    def __str__(self):
        return f"Q: {self.question[:50]}..."


class TestSession(models.Model):
    """Model to track test sessions"""
    flashcard_set = models.ForeignKey(FlashcardSet, on_delete=models.CASCADE, related_name='test_sessions')
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    score = models.IntegerField(null=True, blank=True)
    total_questions = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-started_at']
    
    def __str__(self):
        return f"Test: {self.flashcard_set.title} - {self.started_at}"


class TestAnswer(models.Model):
    """Model to store answers during a test session"""
    test_session = models.ForeignKey(TestSession, on_delete=models.CASCADE, related_name='answers')
    flashcard = models.ForeignKey(Flashcard, on_delete=models.CASCADE)
    user_answer = models.TextField()
    is_correct = models.BooleanField(default=False)
    answered_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Answer for: {self.flashcard.question[:30]}..."

