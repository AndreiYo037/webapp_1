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
from django.conf import settings
from datetime import timedelta
import json
import hmac
import hashlib
try:
    import stripe
    STRIPE_AVAILABLE = True
except ImportError:
    STRIPE_AVAILABLE = False
    stripe = None

from .models import UserProfile, FileUpload, FlashcardSet, Flashcard, Subscription, EmailVerificationToken
from .file_processor import (
    extract_text_from_file, extract_all_images_from_pdf, extract_all_images_from_docx,
    match_images_to_flashcards, auto_crop_image_for_question,
    generate_flashcards_from_text, calculate_flashcard_count
)
from .visual_region_service import VisualRegionPipeline
import os
from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile
from .email_utils import (
    send_verification_email, send_password_reset_email, 
    send_subscription_confirmation_email, send_subscription_cancelled_email,
    send_subscription_renewal_email
)

# Configure Stripe if available
if STRIPE_AVAILABLE:
    stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', None)

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
        
        # Process file and generate flashcards with semantic matching and image generation
        try:
            # Use advanced file processing that supports images, Excel, and more
            file_path = file_upload.file.path
            text_content = extract_text_from_file(file_path, file_upload.file_type)
            
            if not text_content or len(text_content.strip()) == 0:
                raise Exception("File is empty or contains no extractable text content.")
            
            # Calculate optimal number of flashcards based on content
            num_flashcards = calculate_flashcard_count(text_content)
            print(f"[INFO] Generating {num_flashcards} flashcards from {len(text_content)} characters of content")
            
            # Generate flashcards using LLM (Groq/Gemini) with fallback to rule-based
            flashcards_data = generate_flashcards_from_text(text_content, num_flashcards)
            
            if not flashcards_data or len(flashcards_data) == 0:
                raise Exception("Failed to generate flashcards. Please check your file content.")
            
            print(f"[SUCCESS] Generated {len(flashcards_data)} flashcards")
            
            # Create flashcard set
            flashcard_set = FlashcardSet.objects.create(
                user=request.user,
                file_upload=file_upload,
                title=uploaded_file.name
            )
            
            # Extract images from document for semantic matching
            file_extension = file_upload.get_file_extension()
            images = []
            
            try:
                print(f"[INFO] Extracting images from {file_extension} file...")
                if file_extension == '.pdf':
                    images = extract_all_images_from_pdf(file_path)
                    print(f"[INFO] Extracted {len(images)} images from PDF")
                elif file_extension in ['.docx', '.doc']:
                    images = extract_all_images_from_docx(file_path)
                    print(f"[INFO] Extracted {len(images)} images from Word document")
                elif file_extension in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp']:
                    # For image files, the image itself is the content
                    from PIL import Image
                    try:
                        img = Image.open(file_path)
                        images = [img]
                        print(f"[INFO] Processing image file directly")
                    except Exception as img_open_err:
                        print(f"[WARNING] Failed to open image file: {str(img_open_err)}")
            except Exception as img_err:
                print(f"[WARNING] Failed to extract images: {str(img_err)}")
                import traceback
                traceback.print_exc()
            
            # Use semantic matching to match images to flashcards
            image_matches = None
            all_detected_regions = []  # Store all detected visual regions for fallback
            
            if images and len(images) > 0:
                print(f"[INFO] Attempting semantic matching for {len(images)} images with {len(flashcards_data)} flashcards...")
                try:
                    # First try: Use visual region pipeline for advanced semantic matching (for PDF/DOCX)
                    if file_extension in ['.pdf', '.docx', '.doc']:
                        pipeline = VisualRegionPipeline()
                        questions = [card['question'] for card in flashcards_data]
                        matches = pipeline.process_document(file_path, file_upload.file_type, questions)
                        
                        # Store all detected regions for potential fallback use
                        all_detected_regions = [region for _, region, _ in matches if region and region.image]
                        
                        # Create a mapping of question index to matched region
                        image_matches = {}
                        for q_idx, region, score in matches:
                            if q_idx < len(flashcards_data) and region and region.image:
                                image_matches[q_idx] = region
                                print(f"[INFO] Matched question {q_idx} to visual region with confidence {score:.2f}")
                        
                        if image_matches:
                            print(f"[SUCCESS] Semantic matching found {len(image_matches)} matches using visual region pipeline")
                        elif all_detected_regions:
                            print(f"[INFO] Visual regions detected but not matched - will use regions in fallback")
                    
                    # Fallback/Second try: Use LLM-based image matching (works for all file types)
                    if not image_matches or len(image_matches) < len(flashcards_data) * 0.5:
                        print(f"[INFO] Using LLM-based image matching as {'fallback' if image_matches else 'primary'} method...")
                        try:
                            # Create temporary file objects for matching
                            from .file_processor import understand_image_with_vision
                            
                            # For image files, use the single image for all flashcards
                            if file_extension in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'] and len(images) == 1:
                                # Single image file - match to all flashcards
                                image_matches = {}
                                for idx in range(len(flashcards_data)):
                                    class SimpleRegion:
                                        def __init__(self, img):
                                            self.image = img
                                    image_matches[idx] = SimpleRegion(images[0])
                                print(f"[INFO] Single image file - assigned to all {len(flashcards_data)} flashcards")
                            else:
                                # Multiple images - use LLM matching
                                image_files_list = [file_upload] * len(images) if len(images) > 0 else []
                                image_matches_list = match_images_to_flashcards(flashcards_data, image_files_list, text_content)
                                if image_matches_list:
                                    if not image_matches:
                                        image_matches = {}
                                    for q_idx, img_idx in image_matches_list:
                                        if img_idx < len(images):
                                            class SimpleRegion:
                                                def __init__(self, img):
                                                    self.image = img
                                            image_matches[q_idx] = SimpleRegion(images[img_idx])
                                    print(f"[SUCCESS] LLM-based matching found {len(image_matches_list)} matches")
                        except Exception as llm_match_err:
                            print(f"[WARNING] LLM-based image matching failed: {str(llm_match_err)}")
                            import traceback
                            traceback.print_exc()
                            
                except Exception as match_err:
                    print(f"[WARNING] Semantic matching failed: {str(match_err)}")
                    import traceback
                    traceback.print_exc()
                
                # Final fallback: Use detected visual regions if available, otherwise round-robin full pages
                if not image_matches or len(image_matches) < len(flashcards_data):
                    if all_detected_regions and len(all_detected_regions) > 0:
                        # Use detected visual regions (cropped sections) in round-robin
                        print(f"[INFO] Using detected visual regions in round-robin distribution (fallback)...")
                        if not image_matches:
                            image_matches = {}
                        for idx in range(len(flashcards_data)):
                            if idx not in image_matches:
                                region_idx = idx % len(all_detected_regions)
                                image_matches[idx] = all_detected_regions[region_idx]
                        print(f"[INFO] Distributed {len(all_detected_regions)} visual regions to {len(flashcards_data)} flashcards")
                    elif images:
                        # Last resort: use full page images (but try to crop them)
                        print(f"[WARNING] No visual regions detected - using full page images as last resort")
                        print(f"[INFO] Using round-robin distribution of full pages as final fallback...")
                        if not image_matches:
                            image_matches = {}
                        for idx in range(len(flashcards_data)):
                            if idx not in image_matches:
                                img_idx = idx % len(images)
                                class SimpleRegion:
                                    def __init__(self, img):
                                        self.image = img
                                image_matches[idx] = SimpleRegion(images[img_idx])
                        print(f"[INFO] Distributed {len(images)} full page images to {len(flashcards_data)} flashcards using round-robin")
            
            # Create flashcards with images
            for idx, card_data in enumerate(flashcards_data):
                flashcard = Flashcard.objects.create(
                    flashcard_set=flashcard_set,
                    question=card_data['question'],
                    answer=card_data['answer'],
                    source_image=file_upload if images else None
                )
                
                # Add cropped image if matched
                if image_matches and idx in image_matches:
                    try:
                        region = image_matches[idx]
                        if region and region.image:
                            # The region.image is already a cropped visual region from the page
                            # Try to further refine it using auto-crop with the question text
                            # This will identify the most relevant part within the visual region
                            cropped_img = auto_crop_image_for_question(region.image, card_data['question'])
                            if not cropped_img:
                                # If auto-crop fails or returns None, use the visual region image directly
                                # This is already a cropped section of the page, not the full page
                                cropped_img = region.image
                                print(f"[INFO] Using visual region image directly for flashcard {idx} (auto-crop not needed or failed)")
                            else:
                                print(f"[INFO] Further refined visual region using auto-crop for flashcard {idx}")
                            
                            # Save cropped image
                            img_buffer = BytesIO()
                            if cropped_img.mode != 'RGB':
                                cropped_img = cropped_img.convert('RGB')
                            cropped_img.save(img_buffer, format='PNG')
                            img_buffer.seek(0)
                            
                            flashcard.cropped_image.save(
                                f'crop_{flashcard.id}.png',
                                ContentFile(img_buffer.read()),
                                save=True
                            )
                            print(f"[SUCCESS] Saved cropped image for flashcard {idx} (question: {card_data['question'][:50]}...)")
                    except Exception as crop_err:
                        print(f"[WARNING] Failed to save cropped image for flashcard {idx}: {str(crop_err)}")
                        import traceback
                        traceback.print_exc()
            
            file_upload.processed = True
            file_upload.save()
            
            # Increment usage count
            profile.increment_usage()
            
            # Create success message with details
            image_count = len([f for f in flashcard_set.flashcards.all() if f.cropped_image]) if flashcard_set else 0
            if image_count > 0:
                messages.success(request, f'Successfully created {len(flashcards_data)} flashcards with {image_count} images using semantic matching!')
            else:
                messages.success(request, f'Successfully created {len(flashcards_data)} flashcards!')
            
            print(f"[SUCCESS] Flashcard generation complete: {len(flashcards_data)} cards, {image_count} with images")
            return redirect('flashcards:view_flashcards', set_id=flashcard_set.id)
        except Exception as e:
            messages.error(request, f'Error processing file: {str(e)}')
            import traceback
            print(f"[ERROR] Upload error: {traceback.format_exc()}")
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


def register(request):
    """User registration with email verification"""
    if request.user.is_authenticated:
        return redirect('flashcards:index')
    
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # UserProfile is automatically created by signal
            # Get the profile that was just created
            profile = user.profile
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
    """Upgrade to premium subscription with Stripe"""
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    
    # Check if Stripe is configured
    if not STRIPE_AVAILABLE:
        messages.error(request, 'Stripe is not installed. Please install it: pip install stripe')
        return redirect('flashcards:index')
    
    stripe_public_key = getattr(settings, 'STRIPE_PUBLIC_KEY', None)
    stripe_secret_key = getattr(settings, 'STRIPE_SECRET_KEY', None)
    
    if not stripe_public_key or not stripe_secret_key:
        messages.error(request, 'Payment system is not configured. Please set STRIPE_PUBLIC_KEY and STRIPE_SECRET_KEY in environment variables.')
        return redirect('flashcards:index')
    
    if request.method == 'POST':
        plan = request.POST.get('plan', 'monthly')
        
        # Plan configurations
        plans = {
            'monthly': {
                'price_id': getattr(settings, 'STRIPE_PRICE_ID_MONTHLY', None),
                'amount': 9.99,
                'name': 'Premium Monthly',
                'interval': 'month'
            }
        }
        
        selected_plan = plans.get(plan, plans['monthly'])
        
        if not selected_plan['price_id']:
            # Fallback: Create Checkout Session with price amount
            try:
                # Create Stripe Checkout Session
                checkout_session = stripe.checkout.Session.create(
                    customer_email=request.user.email,
                    payment_method_types=['card'],
                    line_items=[{
                        'price_data': {
                            'currency': 'usd',
                            'product_data': {
                                'name': selected_plan['name'],
                                'description': 'Unlimited flashcard generations',
                            },
                            'unit_amount': int(selected_plan['amount'] * 100),  # Convert to cents
                            'recurring': {
                                'interval': selected_plan['interval'],
                            },
                        },
                        'quantity': 1,
                    }],
                    mode='subscription',
                    success_url=request.build_absolute_uri('/subscription/success/?session_id={CHECKOUT_SESSION_ID}'),
                    cancel_url=request.build_absolute_uri('/subscription/cancel/'),
                    metadata={
                        'user_id': request.user.id,
                        'plan': plan,
                    },
                )
                
                return redirect(checkout_session.url)
            except Exception as e:
                messages.error(request, f'Error creating payment session: {str(e)}')
                return redirect('flashcards:upgrade')
        else:
            # Use price ID if configured
            try:
                checkout_session = stripe.checkout.Session.create(
                    customer_email=request.user.email,
                    payment_method_types=['card'],
                    line_items=[{
                        'price': selected_plan['price_id'],
                        'quantity': 1,
                    }],
                    mode='subscription',
                    success_url=request.build_absolute_uri('/subscription/success/?session_id={CHECKOUT_SESSION_ID}'),
                    cancel_url=request.build_absolute_uri('/subscription/cancel/'),
                    metadata={
                        'user_id': request.user.id,
                        'plan': plan,
                    },
                )
                
                return redirect(checkout_session.url)
            except Exception as e:
                messages.error(request, f'Error creating payment session: {str(e)}')
                return redirect('flashcards:upgrade')
    
    return render(request, 'flashcards/upgrade.html', {
        'profile': profile,
        'remaining': profile.get_remaining_free_generations(),
        'stripe_public_key': stripe_public_key,
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


@login_required
def subscription_success(request):
    """Handle successful subscription payment"""
    session_id = request.GET.get('session_id')
    
    if not session_id:
        messages.error(request, 'Invalid session.')
        return redirect('flashcards:index')
    
    try:
        # Retrieve the Checkout Session
        session = stripe.checkout.Session.retrieve(session_id)
        
        if session.payment_status == 'paid':
            # Get or create subscription
            stripe_subscription_id = session.subscription
            user_id = int(session.metadata.get('user_id'))
            user = User.objects.get(id=user_id)
            
            # Check if subscription already exists
            subscription, created = Subscription.objects.get_or_create(
                stripe_subscription_id=stripe_subscription_id,
                defaults={
                    'user': user,
                    'plan_name': 'premium',
                    'amount_paid': session.amount_total / 100,  # Convert from cents
                    'expires_at': timezone.now() + timedelta(days=30),
                    'is_active': True,
                    'status': 'active',
                    'auto_renew': True,
                    'payment_id': session.payment_intent,
                }
            )
            
            if not created:
                # Update existing subscription
                subscription.is_active = True
                subscription.status = 'active'
                subscription.auto_renew = True
                subscription.save()
            
            # Update user profile
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.is_premium = True
            profile.premium_expires_at = subscription.expires_at
            profile.save()
            
            # Send confirmation email
            try:
                send_subscription_confirmation_email(user, subscription)
            except Exception as e:
                messages.warning(request, f'Subscription activated, but email failed: {str(e)}')
            
            messages.success(request, 'Thank you for subscribing! You now have unlimited flashcard generations.')
        else:
            messages.warning(request, 'Payment is still processing. Please wait a moment.')
        
    except Exception as e:
        messages.error(request, f'Error processing subscription: {str(e)}')
    
    return redirect('flashcards:account')


@login_required
def subscription_cancel(request):
    """Handle cancelled subscription payment"""
    messages.info(request, 'Subscription payment was cancelled. You can try again anytime.')
    return redirect('flashcards:upgrade')


@csrf_exempt
@require_http_methods(["POST"])
def payment_webhook(request):
    """Handle Stripe webhooks for subscription events"""
    if not STRIPE_AVAILABLE:
        return JsonResponse({'status': 'error', 'message': 'Stripe not available'}, status=400)
    
    webhook_secret = getattr(settings, 'STRIPE_WEBHOOK_SECRET', None)
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    try:
        if webhook_secret and sig_header:
            # Verify webhook signature
            event = stripe.Webhook.construct_event(
                payload, sig_header, webhook_secret
            )
        else:
            # For development, parse without verification
            event_data = json.loads(payload)
            # Create a simple event-like object
            class Event:
                def __init__(self, data):
                    self.type = data.get('type')
                    self.data = type('Data', (), {
                        'object': data.get('data', {}).get('object', {})
                    })()
            event = Event(event_data)
        
        # Handle the event
        if event.type == 'checkout.session.completed':
            session = event.data.object
            # Subscription will be created in subscription_success view
            pass
            
        elif event.type == 'customer.subscription.created':
            subscription_obj = event.data.object
            # Find or create subscription
            try:
                subscription = Subscription.objects.get(stripe_subscription_id=subscription_obj.id)
                subscription.is_active = True
                subscription.status = 'active'
                subscription.save()
            except Subscription.DoesNotExist:
                pass
        
        elif event.type == 'customer.subscription.updated':
            subscription_obj = event.data.object
            try:
                subscription = Subscription.objects.get(stripe_subscription_id=subscription_obj.id)
                
                # Update subscription status
                if subscription_obj.status == 'active':
                    subscription.is_active = True
                    subscription.status = 'active'
                    # Update expiration based on current_period_end
                    if hasattr(subscription_obj, 'current_period_end') and subscription_obj.current_period_end:
                        from datetime import datetime
                        subscription.expires_at = datetime.fromtimestamp(
                            subscription_obj.current_period_end, tz=timezone.utc
                        )
                elif subscription_obj.status == 'canceled':
                    subscription.cancel()
                
                subscription.save()
            except Subscription.DoesNotExist:
                pass
        
        elif event.type == 'customer.subscription.deleted':
            subscription_obj = event.data.object
            try:
                subscription = Subscription.objects.get(stripe_subscription_id=subscription_obj.id)
                subscription.cancel()
                send_subscription_cancelled_email(subscription.user, subscription)
            except Subscription.DoesNotExist:
                pass
        
        elif event.type == 'invoice.payment_succeeded':
            invoice = event.data.object
            if invoice.subscription:
                try:
                    subscription = Subscription.objects.get(stripe_subscription_id=invoice.subscription)
                    # Renew subscription
                    if hasattr(invoice, 'period_end') and invoice.period_end:
                        from datetime import datetime
                        subscription.expires_at = datetime.fromtimestamp(
                            invoice.period_end, tz=timezone.utc
                        )
                    else:
                        subscription.renew()
                    subscription.save()
                    
                    # Update user profile
                    profile = subscription.user.profile
                    profile.is_premium = True
                    profile.premium_expires_at = subscription.expires_at
                    profile.save()
                    
                    send_subscription_renewal_email(subscription.user, subscription)
                except Subscription.DoesNotExist:
                    pass
        
        elif event.type == 'invoice.payment_failed':
            invoice = event.data.object
            if invoice.subscription:
                try:
                    subscription = Subscription.objects.get(stripe_subscription_id=invoice.subscription)
                    subscription.status = 'pending_renewal'
                    subscription.save()
                except Subscription.DoesNotExist:
                    pass
        
        return JsonResponse({'status': 'success'})
    
    except ValueError as e:
        # Invalid payload
        return JsonResponse({'status': 'error', 'message': 'Invalid payload'}, status=400)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return JsonResponse({'status': 'error', 'message': 'Invalid signature'}, status=400)
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

