from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    # Make sure 'board.urls' is correctly defined
    path('', include('board.urls')),

    path('messageboard/', include('board.urls', namespace='board')),
]

static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    

urlpatterns = [
    path('admin/', admin.site.urls),
]
