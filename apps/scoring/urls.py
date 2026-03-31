# scoring/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('scoring/', views.scoring_view, name='scoring'),
]