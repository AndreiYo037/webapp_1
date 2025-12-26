"""
URL configuration for flashcard_app project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),  # Django allauth URLs for Google OAuth
    path('', include('flashcards.urls')),
]

# Serve static and media files in production (WhiteNoise handles static, but media needs special handling)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    if hasattr(settings, 'STATIC_ROOT') and settings.STATIC_ROOT:
        urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
else:
    # In production, static files are served by WhiteNoise
    # Media files may need external storage (S3, Cloudinary) for cloud platforms
    # For now, we'll serve media files if MEDIA_ROOT exists (may not work on all platforms)
    if hasattr(settings, 'MEDIA_ROOT') and settings.MEDIA_ROOT.exists():
        urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


