from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.report_view, name='report'),
    path('generate-pdf/', views.generate_pdf_report, name='generate_pdf'),
]