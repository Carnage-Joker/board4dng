from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from django.conf.urls.static import static
from board import views
from django.shortcuts import render

# Custom error handlers


def custom_404_view(request, exception):
    return render(request, 'board/404.html', status=404)


def custom_500_view(request):
    return render(request, 'board/500.html', status=500)


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.welcome, name='welcome'),
    path('messageboard/', include('board.urls')),
    path('pwa/', include('pwa.urls')),  # Explicit path for PWA URLs
]
# Only serve static and media files in development (debug mode)
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL,
                          document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)

handler404 = 'messageboard.urls.custom_404_view'
handler500 = 'messageboard.urls.custom_500_view'
