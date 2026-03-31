from django.urls import path
from . import views

app_name = 'credit'

urlpatterns = [
    path('client/<int:client_id>/applications/', 
         views.client_applications, 
         name='client_applications'),
    path('client/<int:client_id>/application/create/', 
         views.application_create, 
         name='application_create'),
     path('application/<int:pk>/',
          views.application_detail,
          name='application_detail'),
    path('application/<int:pk>/score/',
         views.application_score,
         name='application_score'),
]