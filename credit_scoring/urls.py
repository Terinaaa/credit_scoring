# credit_scoring/urls.py
from django.contrib import admin
from django.urls import path, include
from apps.users.views import index_view
from apps.users import views as user_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', index_view, name='index'),
    path('users/', include('apps.users.urls')),
]