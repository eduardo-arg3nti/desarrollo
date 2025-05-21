"""
URL configuration for restaurante_core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include 
from django.views.generic import TemplateView # Para la vista de inicio simple
from django.contrib.auth import views as auth_views # Para LoginView y LogoutView

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # App URLs
    path('stock/', include('stock.urls', namespace='stock')),
    path('ventas/', include('ventas.urls', namespace='ventas')),
    path('mesas/', include('gestion_mesas.urls', namespace='gestion_mesas')),
    
    # Auth URLs
    # Usamos django.contrib.auth.urls para la mayoría de las URLs de autenticación
    # path('accounts/', include('django.contrib.auth.urls')),
    # Pero para personalizar, definimos las más comunes aquí:
    path('accounts/login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),

    # App de Informes
    path('informes/', include('informes.urls', namespace='informes')),

    # Página de inicio simple
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
]
