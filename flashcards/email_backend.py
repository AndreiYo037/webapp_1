"""
Custom email backend with retry logic and better error handling for Railway deployments
"""
import time
import socket
from django.core.mail.backends.smtp import EmailBackend
from django.conf import settings


class RetrySMTPEmailBackend(EmailBackend):
    """
    Custom SMTP backend with retry logic and better connection handling.
    Designed to work better with Railway and other cloud platforms.
    """
    
    def __init__(self, *args, **kwargs):
        # Set connection timeout (default 30 seconds)
        self.timeout = getattr(settings, 'EMAIL_TIMEOUT', 30)
        # Number of retry attempts
        self.max_retries = getattr(settings, 'EMAIL_MAX_RETRIES', 3)
        # Delay between retries (seconds)
        self.retry_delay = getattr(settings, 'EMAIL_RETRY_DELAY', 2)
        
        super().__init__(*args, **kwargs)
    
    def open(self):
        """
        Open SMTP connection with retry logic
        """
        if self.connection:
            return False
        
        last_error = None
        for attempt in range(1, self.max_retries + 1):
            try:
                print(f"[EMAIL] Attempting SMTP connection (attempt {attempt}/{self.max_retries})...")
                
                # Create connection with timeout
                connection = self.connection_class(
                    self.host,
                    self.port,
                    timeout=self.timeout
                )
                
                # Enable TLS if configured
                if self.use_tls:
                    connection.starttls()
                
                # Authenticate if credentials provided
                if self.username and self.password:
                    connection.login(self.username, self.password)
                
                self.connection = connection
                print(f"[EMAIL] SMTP connection established successfully")
                return True
                
            except socket.gaierror as e:
                # DNS resolution error
                error_msg = f"DNS resolution failed: {str(e)}"
                print(f"[EMAIL ERROR] {error_msg}")
                last_error = Exception(f"Could not resolve SMTP host '{self.host}': {error_msg}")
                
            except socket.timeout as e:
                # Connection timeout
                error_msg = f"Connection timeout after {self.timeout}s: {str(e)}"
                print(f"[EMAIL ERROR] {error_msg}")
                last_error = Exception(f"Connection to {self.host}:{self.port} timed out: {error_msg}")
                
            except OSError as e:
                # Network unreachable or connection refused
                error_code = getattr(e, 'errno', None)
                if error_code == 101:  # Network is unreachable
                    error_msg = f"Network unreachable: {str(e)}"
                    print(f"[EMAIL ERROR] {error_msg}")
                    last_error = Exception(f"Cannot reach {self.host}:{self.port}. Railway may be blocking outbound SMTP connections. Consider using a transactional email service like Resend or SendGrid.")
                elif error_code == 111:  # Connection refused
                    error_msg = f"Connection refused: {str(e)}"
                    print(f"[EMAIL ERROR] {error_msg}")
                    last_error = Exception(f"Connection refused by {self.host}:{self.port}: {error_msg}")
                else:
                    error_msg = f"Network error: {str(e)}"
                    print(f"[EMAIL ERROR] {error_msg}")
                    last_error = Exception(f"Network error connecting to {self.host}:{self.port}: {error_msg}")
                
            except Exception as e:
                error_msg = str(e)
                print(f"[EMAIL ERROR] Connection failed: {error_msg}")
                last_error = e
            
            # Wait before retrying (exponential backoff)
            if attempt < self.max_retries:
                wait_time = self.retry_delay * attempt
                print(f"[EMAIL] Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
        
        # All retries failed
        if last_error:
            raise last_error
        raise Exception(f"Failed to connect to SMTP server after {self.max_retries} attempts")
    
    def send_messages(self, email_messages):
        """
        Send messages with retry logic
        """
        if not email_messages:
            return 0
        
        last_error = None
        for attempt in range(1, self.max_retries + 1):
            try:
                # Ensure connection is open
                if not self.connection:
                    self.open()
                
                # Send messages using parent class method
                return super().send_messages(email_messages)
                
            except (socket.timeout, OSError, socket.gaierror) as e:
                error_code = getattr(e, 'errno', None)
                if error_code == 101:  # Network is unreachable
                    error_msg = f"Network unreachable during send: {str(e)}"
                    print(f"[EMAIL ERROR] {error_msg}")
                    last_error = Exception(f"Cannot reach SMTP server. Railway may be blocking outbound SMTP connections. Consider using Resend or SendGrid.")
                else:
                    error_msg = f"Network error during send: {str(e)}"
                    print(f"[EMAIL ERROR] {error_msg}")
                    last_error = e
                
                # Close connection on error
                if self.connection:
                    try:
                        self.connection.close()
                    except:
                        pass
                    self.connection = None
                
                # Retry if not last attempt
                if attempt < self.max_retries:
                    wait_time = self.retry_delay * attempt
                    print(f"[EMAIL] Retrying send in {wait_time} seconds...")
                    time.sleep(wait_time)
                    
            except Exception as e:
                error_msg = str(e)
                print(f"[EMAIL ERROR] Send failed: {error_msg}")
                last_error = e
                
                # Close connection on error
                if self.connection:
                    try:
                        self.connection.close()
                    except:
                        pass
                    self.connection = None
                
                # Retry if not last attempt
                if attempt < self.max_retries:
                    wait_time = self.retry_delay * attempt
                    print(f"[EMAIL] Retrying send in {wait_time} seconds...")
                    time.sleep(wait_time)
        
        # All retries failed
        if last_error:
            raise last_error
        raise Exception(f"Failed to send email after {self.max_retries} attempts")

