from django.contrib import admin
from .models import UserProfile, FileUpload, FlashcardSet, Flashcard, TestSession, Subscription, EmailVerificationToken


@admin.register(FileUpload)
class FileUploadAdmin(admin.ModelAdmin):
    list_display = ['filename', 'file_type', 'uploaded_at', 'processed']
    list_filter = ['file_type', 'processed', 'uploaded_at']


@admin.register(FlashcardSet)
class FlashcardSetAdmin(admin.ModelAdmin):
    list_display = ['title', 'file_upload', 'created_at']
    list_filter = ['created_at']


@admin.register(Flashcard)
class FlashcardAdmin(admin.ModelAdmin):
    list_display = ['question', 'flashcard_set', 'created_at']
    list_filter = ['flashcard_set', 'created_at']


@admin.register(EmailVerificationToken)
class EmailVerificationTokenAdmin(admin.ModelAdmin):
    list_display = ['user', 'token', 'created_at', 'expires_at', 'is_used']
    list_filter = ['is_used', 'created_at']
    search_fields = ['user__username', 'user__email', 'token']
    readonly_fields = ['token', 'created_at']


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'flashcard_generations_used', 'is_premium', 'email_verified', 'premium_expires_at']
    list_filter = ['is_premium', 'email_verified', 'created_at']
    search_fields = ['user__username', 'user__email']


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['user', 'plan_name', 'amount_paid', 'payment_date', 'expires_at', 'status', 'is_active', 'auto_renew']
    list_filter = ['is_active', 'status', 'plan_name', 'auto_renew', 'payment_date']
    search_fields = ['user__username', 'payment_id', 'stripe_subscription_id']
    readonly_fields = ['payment_date', 'cancelled_at']


@admin.register(TestSession)
class TestSessionAdmin(admin.ModelAdmin):
    list_display = ['flashcard_set', 'started_at', 'score', 'total_questions']
    list_filter = ['started_at']

