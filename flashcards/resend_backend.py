"""
Resend email backend for Django
Uses Resend API instead of SMTP - perfect for Railway and cloud platforms
"""
import resend
from django.core.mail.backends.base import BaseEmailBackend
from django.conf import settings
from django.core.mail.message import EmailMessage


class ResendEmailBackend(BaseEmailBackend):
    """
    Email backend using Resend API
    Perfect for Railway deployments where SMTP is blocked
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.resend_api_key = getattr(settings, 'RESEND_API_KEY', None)
        
        if not self.resend_api_key:
            raise ValueError("RESEND_API_KEY is required for ResendEmailBackend. Set RESEND_API_KEY in environment variables.")
        
        # Initialize Resend client
        resend.api_key = self.resend_api_key
        print(f"[RESEND] Backend initialized with API key (length: {len(self.resend_api_key)})")
    
    def send_messages(self, email_messages):
        """
        Send email messages using Resend API
        """
        if not email_messages:
            return 0
        
        sent_count = 0
        for message in email_messages:
            if isinstance(message, EmailMessage):
                try:
                    # Extract email data
                    to_emails = message.to
                    subject = message.subject
                    body = message.body
                    
                    # Get HTML content if available
                    html_content = None
                    if hasattr(message, 'alternatives') and message.alternatives:
                        for content, mimetype in message.alternatives:
                            if mimetype == 'text/html':
                                html_content = content
                                break
                    
                    # Use HTML if available, otherwise plain text
                    email_content = html_content if html_content else body
                    
                    # Get from email (use message.from_email, then DEFAULT_FROM_EMAIL, then fallback)
                    from_email = message.from_email or getattr(settings, 'DEFAULT_FROM_EMAIL', 'onboarding@resend.dev')
                    
                    # Send via Resend API
                    params = {
                        "from": from_email,
                        "to": to_emails,
                        "subject": subject,
                    }
                    
                    if html_content:
                        params["html"] = html_content
                        params["text"] = body  # Include plain text as fallback
                    else:
                        params["text"] = body
                    
                    print(f"[RESEND] Sending email to {to_emails} from {params['from']}...")
                    email_response = resend.Emails.send(params)
                    
                    if email_response and hasattr(email_response, 'id'):
                        print(f"[RESEND SUCCESS] Email sent successfully. ID: {email_response.id}")
                        sent_count += 1
                    else:
                        print(f"[RESEND WARNING] Email sent but no ID returned: {email_response}")
                        sent_count += 1
                        
                except Exception as e:
                    error_msg = str(e)
                    print(f"[RESEND ERROR] Failed to send email: {error_msg}")
                    import traceback
                    print(f"[RESEND ERROR] Traceback: {traceback.format_exc()}")
                    
                    # Don't fail silently if fail_silently is False
                    if not self.fail_silently:
                        raise
        return sent_count

