"""Custom middleware to handle CSRF trusted origins dynamically"""
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin


class CSRFTrustedOriginMiddleware(MiddlewareMixin):
    """Dynamically add request origin to CSRF_TRUSTED_ORIGINS"""
    
    def process_request(self, request):
        """Add the request origin to CSRF_TRUSTED_ORIGINS if not already present"""
        if request.is_secure() or request.META.get('HTTP_X_FORWARDED_PROTO') == 'https':
            origin = request.META.get('HTTP_ORIGIN') or request.META.get('HTTP_HOST')
            if origin:
                # Construct full origin
                if origin.startswith('http'):
                    full_origin = origin
                else:
                    protocol = 'https' if request.is_secure() or request.META.get('HTTP_X_FORWARDED_PROTO') == 'https' else 'http'
                    full_origin = f'{protocol}://{origin}'
                
                # Add to CSRF_TRUSTED_ORIGINS if not already there
                if full_origin not in settings.CSRF_TRUSTED_ORIGINS:
                    settings.CSRF_TRUSTED_ORIGINS.append(full_origin)
        
        return None

