from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from formulario import views
from django.contrib.auth.views import LogoutView



urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('formulario.urls')),  # ¡Incluye las URLs de tu app!
    path('accounts/', include('django.contrib.auth.urls')),  # URLs de login/logout
    path('accounts/signup/', views.signup, name='signup'),  # Añade esto
    path('accounts/logout/', views.custom_logout, name='logout'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)