from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.utils.crypto import get_random_string
import os
import secrets


class EmailVerificationToken(models.Model):
    """Model to store email verification tokens"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='email_verification_tokens')
    token = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Email verification for {self.user.username}"
    
    def is_valid(self):
        """Check if token is still valid"""
        return not self.is_used and timezone.now() < self.expires_at
    
    @staticmethod
    def generate_token(user):
        """Generate a new verification token"""
        token = secrets.token_urlsafe(32)
        expires_at = timezone.now() + timezone.timedelta(days=7)  # Token valid for 7 days
        return EmailVerificationToken.objects.create(
            user=user,
            token=token,
            expires_at=expires_at
        )


class UserProfile(models.Model):
    """Extended user profile to track usage and subscription"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    flashcard_generations_used = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    is_premium = models.BooleanField(default=False)
    premium_expires_at = models.DateTimeField(null=True, blank=True)
    email_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {'Premium' if self.is_premium else 'Free'}"
    
    def can_generate_flashcards(self):
        """Check if user can generate more flashcards"""
        if self.is_premium and (not self.premium_expires_at or self.premium_expires_at > timezone.now()):
            return True
        return self.flashcard_generations_used < 3
    
    def get_remaining_free_generations(self):
        """Get remaining free generations"""
        if self.is_premium:
            return "Unlimited"
        return max(0, 3 - self.flashcard_generations_used)
    
    def increment_usage(self):
        """Increment flashcard generation count"""
        if not self.is_premium:
            self.flashcard_generations_used += 1
            self.save()


class FileUpload(models.Model):
    """Model to store uploaded files"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='file_uploads')
    file = models.FileField(upload_to='uploads/')
    filename = models.CharField(max_length=255)
    file_type = models.CharField(max_length=50)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    processed = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return self.filename
    
    def get_file_extension(self):
        return os.path.splitext(self.filename)[1].lower()


class FlashcardSet(models.Model):
    """Model to store a set of flashcards generated from a file"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='flashcard_sets')
    file_upload = models.ForeignKey(FileUpload, on_delete=models.CASCADE, related_name='flashcard_sets')
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
    source_image = models.ForeignKey('FileUpload', on_delete=models.SET_NULL, blank=True, null=True, related_name='flashcards')
    cropped_image = models.ImageField(upload_to='flashcard_crops/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['id']
    
    def __str__(self):
        return f"Q: {self.question[:50]}..."


class Subscription(models.Model):
    """Model to track user subscriptions"""
    SUBSCRIPTION_STATUS_CHOICES = [
        ('active', 'Active'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
        ('pending_renewal', 'Pending Renewal'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscriptions')
    plan_name = models.CharField(max_length=50, default='premium')
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    status = models.CharField(max_length=20, choices=SUBSCRIPTION_STATUS_CHOICES, default='active')
    auto_renew = models.BooleanField(default=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    payment_id = models.CharField(max_length=255, blank=True, null=True)  # For payment gateway tracking
    stripe_subscription_id = models.CharField(max_length=255, blank=True, null=True)  # Stripe subscription ID
    webhook_events = models.JSONField(default=dict, blank=True)  # Store webhook event data
    
    class Meta:
        ordering = ['-payment_date']
    
    def __str__(self):
        return f"{self.user.username} - {self.plan_name} - {self.get_status_display()}"
    
    def cancel(self):
        """Cancel the subscription"""
        self.is_active = False
        self.status = 'cancelled'
        self.auto_renew = False
        self.cancelled_at = timezone.now()
        self.save()
        
        # Update user profile
        profile = self.user.profile
        profile.is_premium = False
        profile.save()
    
    def renew(self, days=30):
        """Renew the subscription"""
        self.expires_at = timezone.now() + timezone.timedelta(days=days)
        self.is_active = True
        self.status = 'active'
        self.auto_renew = True
        self.cancelled_at = None
        self.save()
        
        # Update user profile
        profile = self.user.profile
        profile.is_premium = True
        profile.premium_expires_at = self.expires_at
        profile.save()
    
    def is_expired(self):
        """Check if subscription is expired"""
        return timezone.now() > self.expires_at


class TestSession(models.Model):
    """Model to track test sessions"""
    flashcard_set = models.ForeignKey(FlashcardSet, on_delete=models.CASCADE, related_name='test_sessions')
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    score = models.IntegerField(default=0)
    total_questions = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-started_at']
    
    def __str__(self):
        return f"Test for {self.flashcard_set.title} - Score: {self.score}/{self.total_questions}"

