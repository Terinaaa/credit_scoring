# apps/clients/urls.py
from django.urls import path
from . import views

app_name = 'clients'

urlpatterns = [
    path('', views.client_list, name='client_list'),
    path('add/', views.client_add, name='client_add'),
    path('<int:pk>/edit/', views.client_edit, name='client_edit'),
    path('<int:pk>/delete/', views.client_delete, name='client_delete'),
    path('api/get-client-by-passport/', views.get_client_by_passport, name='api_get_client_by_passport'),
    path('<int:pk>/data/', views.client_data_view, name='client_data'),
]