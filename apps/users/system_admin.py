# apps/users/system_admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User
from django import forms
from django.contrib import messages
from django.urls import path
from django.shortcuts import render, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.http import JsonResponse
import os
import subprocess
from pathlib import Path

class SystemAdminSite(admin.AdminSite):
    """Кастомная админка для системного администратора"""
    site_header = 'Системное администрирование'
    site_title = 'Управление системой'
    index_title = 'Панель системного администратора'

class MLModelAdmin(admin.ModelAdmin):
    """Админка для управления ML-моделью"""
    
    def has_add_permission(self, request):
        return False  # Нельзя добавлять записи
    
    def has_delete_permission(self, request, obj=None):
        return False  # Нельзя удалять
    
    def changelist_view(self, request, extra_context=None):
        """Кастомная страница для управления ML-моделью"""
        extra_context = extra_context or {}
        
        # Получаем информацию о текущей модели
        model_dir = Path(__file__).resolve().parent.parent.parent / 'ml_model' / 'models'
        model_files = list(model_dir.glob('*.pkl')) if model_dir.exists() else []
        
        model_info = []
        for f in model_files:
            stat = f.stat()
            model_info.append({
                'name': f.name,
                'size': f"{stat.st_size / 1024 / 1024:.2f} МБ",
                'modified': f.stat().st_mtime,
                'path': str(f)
            })
        
        extra_context['models'] = model_info
        extra_context['model_dir'] = str(model_dir)
        
        return render(request, 'admin/system/ml_model.html', extra_context)
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('retrain/', self.admin_site.admin_view(self.retrain_model), name='retrain-model'),
            path('upload-model/', self.admin_site.admin_view(self.upload_model), name='upload-model'),
        ]
        return custom_urls + urls
    
    def retrain_model(self, request):
        """Запуск переобучения модели"""
        if request.method == 'POST':
            try:
                # Запускаем скрипт обучения
                script_path = Path(__file__).resolve().parent.parent.parent / 'ml_model' / 'train.py'
                result = subprocess.run(
                    ['python', str(script_path)], 
                    capture_output=True, 
                    text=True
                )
                
                if result.returncode == 0:
                    messages.success(request, 'Модель успешно переобучена!')
                else:
                    messages.error(request, f'Ошибка при обучении: {result.stderr}')
            except Exception as e:
                messages.error(request, f'Ошибка: {e}')
            
            return redirect('..')
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    def upload_model(self, request):
        """Загрузка новой версии модели"""
        if request.method == 'POST' and request.FILES.get('model_file'):
            model_file = request.FILES['model_file']
            
            # Сохраняем файл в директорию моделей
            model_dir = Path(__file__).resolve().parent.parent.parent / 'ml_model' / 'models'
            model_dir.mkdir(parents=True, exist_ok=True)
            
            file_path = model_dir / model_file.name
            
            with open(file_path, 'wb+') as destination:
                for chunk in model_file.chunks():
                    destination.write(chunk)
            
            messages.success(request, f'Модель {model_file.name} успешно загружена')
            return redirect('..')
        
        return JsonResponse({'error': 'Invalid request'}, status=400)

class SystemConfigAdmin(admin.ModelAdmin):
    """Админка для системных настроек"""
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def changelist_view(self, request, extra_context=None):
        """Страница с системными настройками"""
        extra_context = extra_context or {}
        
        # Собираем информацию о системе
        import django
        import xgboost
        import joblib
        import platform
        
        system_info = {
            'django_version': django.get_version(),
            'python_version': platform.python_version(),
            'xgboost_version': xgboost.__version__,
            'joblib_version': joblib.__version__,
            'os': platform.system(),
            'processor': platform.processor(),
        }
        
        extra_context['system_info'] = system_info
        
        return render(request, 'admin/system/config.html', extra_context)

system_admin_site = SystemAdminSite(name='system_admin')
# Регистрируем модели для системного админа
# Здесь можно добавить регистрацию только тех моделей, которые нужны системному админу
# Например, модель ScoringResult для просмотра статистики