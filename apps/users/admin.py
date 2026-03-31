# apps/users/admin.py
from django.contrib import admin
from .models import User, Role, EmployeePosition
from .db_admin import DBUserAdmin
from .system_admin import SystemAdminSite, MLModelAdmin, SystemConfigAdmin

# Регистрируем модель User с админкой для БД-администратора
admin.site.register(User, DBUserAdmin)

# Регистрируем остальные модели
@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

@admin.register(EmployeePosition)
class EmployeePositionAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

# Создаем отдельный сайт для системного администратора
system_admin_site = SystemAdminSite(name='system_admin')

# Регистрируем модели на системном сайте
# Здесь можно добавить те модели, которые нужны системному администратору