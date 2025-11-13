from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# URLs principales
urlpatterns = [
    path('admin/', admin.site.urls),
    
    # URLs de Keycloak (login, logout, callback)
    path('auth/', include('django_keycloak_auth.urls')),
    
    # URLs de l'app home
    path('', include('home.urls')),
]

# Servir les fichiers statiques et media en développement
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)