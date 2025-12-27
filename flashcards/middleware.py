"""Custom middleware to handle CSRF trusted origins dynamically for Railway"""
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin


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
                # Add to CSRF_TRUSTED_ORIGINS if not already present
                if full_origin not in settings.CSRF_TRUSTED_ORIGINS:
                    # Use a list that we can modify
                    if not hasattr(settings, '_csrf_trusted_origins_dynamic'):
                        settings._csrf_trusted_origins_dynamic = list(settings.CSRF_TRUSTED_ORIGINS)
                    settings._csrf_trusted_origins_dynamic.append(full_origin)
                    # Update the actual setting (this works because settings is a LazyObject)
                    settings.CSRF_TRUSTED_ORIGINS = settings._csrf_trusted_origins_dynamic
        
        return None

