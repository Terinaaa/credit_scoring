# apps/users/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('registration/', views.registration_start_view, name='registration_start'),
    path('registration/complete/', views.registration_complete_view, name='registration_complete'),
    path('account/', views.personal_account_view, name='personal_account'),
    path('debug-auth/', views.debug_auth, name='debug_auth'),
]