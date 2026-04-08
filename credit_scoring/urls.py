# credit_scoring/urls.py
from django.contrib import admin
from django.urls import path, include
from apps.users.views import index_view
from apps.users import views as user_views
from apps.users.system_admin import system_admin_site

urlpatterns = [
    path('admin/', admin.site.urls),  # Стандартная админка для БД-администратора
    path('system-admin/', system_admin_site.urls),  # Админка для системного администратора
    path('', index_view, name='index'),
    path('users/', include('apps.users.urls')),
    path('clients/', include('apps.clients.urls')),
    path('scoring/', include('apps.scoring.urls')),
    path('credit/', include('apps.credit.urls')),
]
