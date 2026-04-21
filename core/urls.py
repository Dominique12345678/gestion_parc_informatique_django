from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Interface natif django (Unfold)
    path('admin/', admin.site.urls),
    
    # Allauth URLs (login, signup, etc.)
    path('accounts/', include('allauth.urls')), 

    # Core App URLs
    path('', include('core_app.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)