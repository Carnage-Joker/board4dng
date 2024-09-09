from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    # added a trailing slash for consistency
    path('home/', include('board.urls')),
    path('messageboard/', include('board.urls')),
    path('', include('pwa.urls')),  # PWA-related URLs
]

# Only serve static and media files in development (debug mode)
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL,
                          document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
