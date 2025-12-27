from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.contrib.auth import login, authenticate, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, PasswordResetForm, SetPasswordForm
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from datetime import timedelta
import json
import hmac
import hashlib
from .models import UserProfile, FileUpload, FlashcardSet, Flashcard, TestSession, Subscription, EmailVerificationToken
from .utils import process_file, generate_flashcards
from .email_utils import (
    send_verification_email, send_password_reset_email, 
    send_subscription_confirmation_email, send_subscription_cancelled_email,
    send_subscription_renewal_email
)

User = get_user_model()


def index(request):
    """Home page showing all flashcard sets"""
    if request.user.is_authenticated:
        flashcard_sets = FlashcardSet.objects.filter(user=request.user)
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        remaining = profile.get_remaining_free_generations()
    else:
        flashcard_sets = FlashcardSet.objects.none()
        remaining = None
    
    return render(request, 'flashcards/index.html', {
        'flashcard_sets': flashcard_sets,
        'remaining_generations': remaining
    })


@login_required
def upload_file(request):
    """Handle file upload"""
    if request.method == 'POST':
        # Get or create user profile
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        
        # Check if user can generate flashcards
        if not profile.can_generate_flashcards():
            messages.error(request, 'You have reached your free limit of 3 flashcard generations. Please upgrade to premium for unlimited access.')
            return redirect('flashcards:upgrade')
        
        if 'file' not in request.FILES:
            messages.error(request, 'No file selected')
            return redirect('flashcards:index')
        
        uploaded_file = request.FILES['file']
        file_upload = FileUpload.objects.create(
            user=request.user,
            file=uploaded_file,
            filename=uploaded_file.name,
            file_type=uploaded_file.content_type or 'unknown'
        )
        
        # Process file and generate flashcards
        try:
            text_content = process_file(file_upload)
            flashcards_data = generate_flashcards(text_content)
            
            # Create flashcard set
            flashcard_set = FlashcardSet.objects.create(
                user=request.user,
                file_upload=file_upload,
                title=uploaded_file.name
            )
            
            # Create flashcards
            for card_data in flashcards_data:
                Flashcard.objects.create(
                    flashcard_set=flashcard_set,
                    question=card_data['question'],
                    answer=card_data['answer']
                )
            
            file_upload.processed = True
            file_upload.save()
            
            # Increment usage count
            profile.increment_usage()
            
            messages.success(request, f'Successfully created {len(flashcards_data)} flashcards!')
            return redirect('flashcards:view_flashcards', set_id=flashcard_set.id)
        except Exception as e:
            messages.error(request, f'Error processing file: {str(e)}')
            return redirect('flashcards:index')
    
    return redirect('flashcards:index')


@login_required
def view_flashcards(request, set_id):
    """View all flashcards in a set"""
    flashcard_set = get_object_or_404(FlashcardSet, id=set_id, user=request.user)
    flashcards = flashcard_set.flashcards.all()
    return render(request, 'flashcards/view_flashcards.html', {
        'flashcard_set': flashcard_set,
        'flashcards': flashcards
    })


@login_required
def start_test(request, set_id):
    """Start a new test session"""
    flashcard_set = get_object_or_404(FlashcardSet, id=set_id, user=request.user)
    flashcards = list(flashcard_set.flashcards.all())
    
    if not flashcards:
        messages.error(request, 'No flashcards available for this set')
        return redirect('flashcards:view_flashcards', set_id=set_id)
    
    # Create test session
    test_session = TestSession.objects.create(
        flashcard_set=flashcard_set,
        total_questions=len(flashcards)
    )
    
    return render(request, 'flashcards/test.html', {
        'flashcard_set': flashcard_set,
        'flashcards': flashcards,
        'test_session': test_session
    })


@require_http_methods(["POST"])
def submit_test(request, set_id):
    """Submit test results"""
    test_session_id = request.POST.get('test_session_id')
    test_session = get_object_or_404(TestSession, id=test_session_id)
    flashcard_set = get_object_or_404(FlashcardSet, id=set_id)
    
    # Get all flashcards for this set
    flashcards = flashcard_set.flashcards.all()
    score = 0
    
    # Calculate score by checking each answer
    for flashcard in flashcards:
        answer_key = f'answer_{flashcard.id}'
        user_answer = request.POST.get(answer_key, '').strip()
        
        if user_answer:
            # Simple keyword matching - in production, you'd want more sophisticated comparison
            # Check if user answer contains key parts of correct answer or vice versa
            user_lower = user_answer.lower()
            correct_lower = flashcard.answer.lower()
            
            # More lenient matching: check for significant word overlap
            user_words = set(user_lower.split())
            correct_words = set(correct_lower.split())
            
            # Remove common words
            common_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'to', 'of', 'and', 'or', 'but', 'in', 'on', 'at', 'for', 'with', 'by'}
            user_words = user_words - common_words
            correct_words = correct_words - common_words
            
            # If there's significant overlap (at least 30% of words match) or substring match
            if user_words and correct_words:
                overlap = len(user_words & correct_words)
                match_ratio = overlap / max(len(user_words), len(correct_words))
                if match_ratio >= 0.3 or user_lower in correct_lower or correct_lower in user_lower:
                    score += 1
    
    test_session.score = score
    test_session.completed_at = timezone.now()
    test_session.save()
    
    # Redirect to results page
    return redirect('flashcards:test_results', session_id=test_session.id)


@login_required
def test_results(request, session_id):
    """View test results"""
    test_session = get_object_or_404(TestSession, id=session_id, flashcard_set__user=request.user)
    return render(request, 'flashcards/test_results.html', {
        'test_session': test_session
    })


def register(request):
    """User registration with email verification"""
    if request.user.is_authenticated:
        return redirect('flashcards:index')
    
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Create user profile
            profile = UserProfile.objects.create(user=user)
            # Send verification email if email is provided
            if user.email:
                try:
                    send_verification_email(user, request)
                    messages.info(request, f'Account created! Please check your email ({user.email}) to verify your account.')
                except Exception as e:
                    messages.warning(request, f'Account created, but verification email could not be sent: {str(e)}')
            else:
                messages.warning(request, 'Please add an email address to your account to receive verification emails.')
            
            # Auto-login after registration
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            if user:
                login(request, user)
                messages.success(request, f'Welcome, {username}! You have 3 free flashcard generations.')
                return redirect('flashcards:index')
    else:
        form = UserCreationForm()
    
    return render(request, 'flashcards/register.html', {'form': form})


def login_view(request):
    """User login"""
    if request.user.is_authenticated:
        return redirect('flashcards:index')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            messages.success(request, f'Welcome back, {username}!')
            return redirect('flashcards:index')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'flashcards/login.html')


from django.contrib.auth import logout as auth_logout

def logout_view(request):
    """User logout"""
    auth_logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('flashcards:index')


@login_required
def upgrade(request):
    """Upgrade to premium subscription"""
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        # In production, integrate with payment gateway (Stripe, PayPal, etc.)
        # For now, simulate payment success
        plan_name = request.POST.get('plan', 'premium')
        amount = request.POST.get('amount', '9.99')
        
        # Create subscription (1 month)
        subscription = Subscription.objects.create(
            user=request.user,
            plan_name=plan_name,
            amount_paid=amount,
            expires_at=timezone.now() + timedelta(days=30),
            is_active=True,
            status='active',
            auto_renew=True
        )
        
        # Update user profile
        profile.is_premium = True
        profile.premium_expires_at = subscription.expires_at
        profile.save()
        
        # Send confirmation email
        try:
            send_subscription_confirmation_email(request.user, subscription)
        except Exception as e:
            messages.warning(request, f'Subscription created, but confirmation email failed: {str(e)}')
        
        messages.success(request, 'Thank you for upgrading to Premium! You now have unlimited flashcard generations.')
        return redirect('flashcards:index')
    
    return render(request, 'flashcards/upgrade.html', {
        'profile': profile,
        'remaining': profile.get_remaining_free_generations()
    })


@login_required
def verify_email(request, token):
    """Verify user email with token"""
    try:
        token_obj = EmailVerificationToken.objects.get(token=token, is_used=False)
        if token_obj.is_valid():
            token_obj.is_used = True
            token_obj.save()
            
            profile = token_obj.user.profile
            profile.email_verified = True
            profile.save()
            
            messages.success(request, 'Email verified successfully!')
        else:
            messages.error(request, 'Verification token has expired. Please request a new one.')
    except EmailVerificationToken.DoesNotExist:
        messages.error(request, 'Invalid verification token.')
    
    return redirect('flashcards:account')


@login_required
def resend_verification_email(request):
    """Resend verification email"""
    if request.user.email:
        try:
            send_verification_email(request.user, request)
            messages.success(request, 'Verification email sent! Please check your inbox.')
        except Exception as e:
            messages.error(request, f'Could not send verification email: {str(e)}')
    else:
        messages.error(request, 'Please add an email address to your account first.')
    
    return redirect('flashcards:account')


def password_reset_request(request):
    """Request password reset"""
    if request.user.is_authenticated:
        return redirect('flashcards:index')
    
    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = User.objects.get(email=email)
                # Generate token
                token = default_token_generator.make_token(user)
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                
                # Send reset email
                send_password_reset_email(user, f"{uid}/{token}", request)
                messages.success(request, 'Password reset email sent! Please check your inbox.')
                return redirect('flashcards:login')
            except User.DoesNotExist:
                messages.error(request, 'No account found with that email address.')
    else:
        form = PasswordResetForm()
    
    return render(request, 'flashcards/password_reset_request.html', {'form': form})


def password_reset_confirm(request, token):
    """Confirm password reset with token"""
    if request.user.is_authenticated:
        return redirect('flashcards:index')
    
    try:
        uid, token_part = token.split('/')
        uid = force_str(urlsafe_base64_decode(uid))
        user = User.objects.get(pk=uid)
        
        if not default_token_generator.check_token(user, token_part):
            messages.error(request, 'Invalid or expired reset token.')
            return redirect('flashcards:password_reset_request')
        
        if request.method == 'POST':
            form = SetPasswordForm(user, request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, 'Password reset successfully! You can now login.')
                return redirect('flashcards:login')
        else:
            form = SetPasswordForm(user)
        
        return render(request, 'flashcards/password_reset_confirm.html', {'form': form})
    except (ValueError, User.DoesNotExist):
        messages.error(request, 'Invalid reset token.')
        return redirect('flashcards:password_reset_request')


@login_required
def cancel_subscription(request, subscription_id):
    """Cancel a subscription"""
    subscription = get_object_or_404(Subscription, id=subscription_id, user=request.user)
    
    if request.method == 'POST':
        subscription.cancel()
        try:
            send_subscription_cancelled_email(request.user, subscription)
        except Exception as e:
            messages.warning(request, f'Subscription cancelled, but email notification failed: {str(e)}')
        
        messages.success(request, 'Subscription cancelled successfully. You can still use premium features until it expires.')
        return redirect('flashcards:account')
    
    return render(request, 'flashcards/cancel_subscription.html', {
        'subscription': subscription
    })


@login_required
def renew_subscription(request, subscription_id):
    """Renew a subscription"""
    subscription = get_object_or_404(Subscription, id=subscription_id, user=request.user)
    
    if request.method == 'POST':
        # In production, process payment here
        days = int(request.POST.get('days', 30))
        subscription.renew(days=days)
        
        try:
            send_subscription_renewal_email(request.user, subscription)
        except Exception as e:
            messages.warning(request, f'Subscription renewed, but email notification failed: {str(e)}')
        
        messages.success(request, f'Subscription renewed for {days} days!')
        return redirect('flashcards:account')
    
    return render(request, 'flashcards/renew_subscription.html', {
        'subscription': subscription
    })


@csrf_exempt
@require_http_methods(["POST"])
def payment_webhook(request):
    """Handle payment webhooks from payment gateway (Stripe, PayPal, etc.)"""
    # This is a template for webhook handling
    # In production, verify webhook signature and handle different event types
    
    try:
        payload = json.loads(request.body)
        event_type = payload.get('type')
        event_data = payload.get('data', {})
        
        # Example: Stripe webhook events
        if event_type == 'customer.subscription.updated':
            # Handle subscription update
            subscription_id = event_data.get('object', {}).get('id')
            customer_id = event_data.get('object', {}).get('customer')
            
            # Find subscription by Stripe ID
            try:
                subscription = Subscription.objects.get(stripe_subscription_id=subscription_id)
                # Update subscription based on webhook data
                subscription.webhook_events[event_type] = payload
                subscription.save()
                
                # Renew if needed
                if subscription.auto_renew and subscription.is_expired():
                    subscription.renew()
                    send_subscription_renewal_email(subscription.user, subscription)
                
            except Subscription.DoesNotExist:
                pass
        
        elif event_type == 'customer.subscription.deleted':
            # Handle subscription cancellation
            subscription_id = event_data.get('object', {}).get('id')
            try:
                subscription = Subscription.objects.get(stripe_subscription_id=subscription_id)
                subscription.cancel()
                send_subscription_cancelled_email(subscription.user, subscription)
            except Subscription.DoesNotExist:
                pass
        
        elif event_type == 'invoice.payment_succeeded':
            # Handle successful payment
            subscription_id = event_data.get('object', {}).get('subscription')
            try:
                subscription = Subscription.objects.get(stripe_subscription_id=subscription_id)
                subscription.renew()
                send_subscription_renewal_email(subscription.user, subscription)
            except Subscription.DoesNotExist:
                pass
        
        return JsonResponse({'status': 'success'})
    
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@login_required
def account(request):
    """User account page"""
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    subscriptions = Subscription.objects.filter(user=request.user).order_by('-payment_date')
    flashcard_sets_count = FlashcardSet.objects.filter(user=request.user).count()
    
    return render(request, 'flashcards/account.html', {
        'profile': profile,
        'subscriptions': subscriptions,
        'flashcard_sets_count': flashcard_sets_count,
        'remaining': profile.get_remaining_free_generations(),
        'now': timezone.now()
    })

