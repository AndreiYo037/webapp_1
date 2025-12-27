"""Email utility functions for flashcards app"""
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.urls import reverse
from django.utils.html import strip_tags
from .models import EmailVerificationToken


def send_verification_email(user, request):
    """Send email verification link to user"""
    # Generate verification token
    token_obj = EmailVerificationToken.generate_token(user)
    
    # Build verification URL
    verification_url = request.build_absolute_uri(
        reverse('flashcards:verify_email', kwargs={'token': token_obj.token})
    )
    
    # Render email template
    html_message = render_to_string('flashcards/emails/verification_email.html', {
        'user': user,
        'verification_url': verification_url,
        'token': token_obj.token,
    })
    
    plain_message = strip_tags(html_message)
    
    # Send email
    send_mail(
        subject='Verify Your Email - Flashcard App',
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False,
    )


def send_password_reset_email(user, reset_token, request):
    """Send password reset link to user"""
    # reset_token is already in format "uid/token"
    reset_url = request.build_absolute_uri(
        reverse('flashcards:password_reset_confirm', kwargs={'token': reset_token})
    )
    
    html_message = render_to_string('flashcards/emails/password_reset_email.html', {
        'user': user,
        'reset_url': reset_url,
    })
    
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject='Password Reset - Flashcard App',
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False,
    )


def send_subscription_confirmation_email(user, subscription):
    """Send subscription confirmation email"""
    html_message = render_to_string('flashcards/emails/subscription_confirmation.html', {
        'user': user,
        'subscription': subscription,
    })
    
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject='Subscription Confirmed - Flashcard App',
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False,
    )


def send_subscription_cancelled_email(user, subscription):
    """Send subscription cancellation email"""
    html_message = render_to_string('flashcards/emails/subscription_cancelled.html', {
        'user': user,
        'subscription': subscription,
    })
    
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject='Subscription Cancelled - Flashcard App',
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False,
    )


def send_subscription_renewal_email(user, subscription):
    """Send subscription renewal email"""
    html_message = render_to_string('flashcards/emails/subscription_renewed.html', {
        'user': user,
        'subscription': subscription,
    })
    
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject='Subscription Renewed - Flashcard App',
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False,
    )

