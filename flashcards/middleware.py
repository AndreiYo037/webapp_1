"""Custom middleware to handle CSRF trusted origins dynamically for Railway"""
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin
import threading


# Thread-local storage for CSRF origins
_thread_locals = threading.local()


def get_csrf_trusted_origins():
    """Get CSRF trusted origins, including dynamically added ones"""
    base_origins = list(settings.CSRF_TRUSTED_ORIGINS)
    dynamic_origins = getattr(_thread_locals, 'csrf_trusted_origins', [])
    return base_origins + dynamic_origins


class CSRFTrustedOriginMiddleware(MiddlewareMixin):
    """Dynamically allow CSRF from Railway domains"""
    
    def process_request(self, request):
        """Allow CSRF if origin matches ALLOWED_HOSTS"""
        # Get the origin from the request
        origin = request.META.get('HTTP_ORIGIN') or request.META.get('HTTP_HOST')
        
        if origin:
            # Construct full origin URL
            if not origin.startswith('http'):
                # Determine protocol
                is_secure = (
                    request.is_secure() or 
                    request.META.get('HTTP_X_FORWARDED_PROTO') == 'https' or
                    request.META.get('HTTP_X_FORWARDED_SSL') == 'on'
                )
                protocol = 'https' if is_secure else 'http'
                full_origin = f'{protocol}://{origin}'
            else:
                full_origin = origin
            
            # Extract host from origin
            if '://' in full_origin:
                host = full_origin.split('://')[1].split('/')[0]
            else:
                host = full_origin
            
            # Check if host is in ALLOWED_HOSTS or if ALLOWED_HOSTS allows all
            if (settings.ALLOWED_HOSTS == ['*'] or host in settings.ALLOWED_HOSTS or 
                any(host.endswith(allowed.replace('*', '')) for allowed in settings.ALLOWED_HOSTS if '*' in allowed)):
                # Store in thread-local for this request
                if not hasattr(_thread_locals, 'csrf_trusted_origins'):
                    _thread_locals.csrf_trusted_origins = []
                if full_origin not in _thread_locals.csrf_trusted_origins:
                    _thread_locals.csrf_trusted_origins.append(full_origin)
                # Also update settings directly (for CSRF middleware)
                if full_origin not in settings.CSRF_TRUSTED_ORIGINS:
                    settings.CSRF_TRUSTED_ORIGINS.append(full_origin)
        
        return None
    
    def process_response(self, request, response):
        """Clean up thread-local storage"""
        if hasattr(_thread_locals, 'csrf_trusted_origins'):
            _thread_locals.csrf_trusted_origins = []
        return response

