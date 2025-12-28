"""Email utility functions for flashcards app"""
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.urls import reverse
from django.utils.html import strip_tags
from .models import EmailVerificationToken


def send_verification_email(user, request):
    """Send email verification link to user"""
    # Check email configuration
    email_backend = getattr(settings, 'EMAIL_BACKEND', '')
    email_host = getattr(settings, 'EMAIL_HOST', '')
    email_user = getattr(settings, 'EMAIL_HOST_USER', '')
    
    print(f"[EMAIL] Attempting to send verification email to {user.email}")
    print(f"[EMAIL] Backend: {email_backend}")
    print(f"[EMAIL] Host: {email_host}")
    print(f"[EMAIL] User: {email_user}")
    
    if 'console' in str(email_backend).lower():
        print("[EMAIL WARNING] Using console backend - emails will not be sent, only printed to logs")
        print("[EMAIL WARNING] Set EMAIL_HOST environment variable to enable SMTP")
    
    if not email_host:
        raise Exception("EMAIL_HOST is not configured. Please set EMAIL_HOST=smtp.gmail.com in Railway environment variables.")
    
    if not user.email:
        raise Exception("User email address is not set.")
    
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
    
    # Send email with detailed error handling
    try:
        send_mail(
            subject='Verify Your Email - Flashcard App',
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        print(f"[EMAIL SUCCESS] Verification email sent to {user.email}")
    except Exception as email_error:
        error_msg = str(email_error)
        print(f"[EMAIL ERROR] Failed to send verification email: {error_msg}")
        
        # Provide helpful error messages
        if 'authentication failed' in error_msg.lower() or 'invalid credentials' in error_msg.lower():
            raise Exception("Email authentication failed. Please check your EMAIL_HOST_PASSWORD (Gmail App Password). Make sure there are no spaces in the App Password.")
        elif 'connection' in error_msg.lower() or 'timeout' in error_msg.lower():
            raise Exception(f"Could not connect to email server ({email_host}). Please check EMAIL_HOST and EMAIL_PORT settings.")
        elif 'smtp' in error_msg.lower():
            raise Exception(f"SMTP error: {error_msg}. Please verify EMAIL_HOST, EMAIL_PORT, and EMAIL_USE_TLS settings.")
        else:
            raise Exception(f"Failed to send email: {error_msg}")


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

