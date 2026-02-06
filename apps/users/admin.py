# apps/users/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User
from django import forms
from django.contrib.auth.forms import UserCreationForm

class CustomUserCreationForm(UserCreationForm):
    """Кастомная форма создания пользователя без обязательного пароля"""
    
    class Meta:
        model = User
        fields = ('username', 'personnel_number', 'first_name', 'last_name', 'role')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Делаем пароль необязательным
        self.fields['password1'].required = False
        self.fields['password2'].required = False
        self.fields['password1'].help_text = _('Оставьте пустым для создания пользователя без пароля')
        self.fields['password2'].help_text = _('Оставьте пустым для создания пользователя без пароля')
    
    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 or password2:
            # Если введен хотя бы один пароль, проверяем оба
            return super().clean_password2()
        return password2
    
    def save(self, commit=True):
        user = super().save(commit=False)
        # Если пароль не введен, устанавливаем непригодный пароль
        if not self.cleaned_data["password1"]:
            user.set_unusable_password()
        if commit:
            user.save()
        return user

class CustomUserAdmin(UserAdmin):
    # Используем кастомную форму создания
    add_form = CustomUserCreationForm
    
    # Порядок полей в форме редактирования существующего пользователя
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Персональная информация'), {'fields': ('first_name', 'last_name', 'middle_name', 'email')}),
        (_('Работа'), {'fields': ('personnel_number', 'position', 'role')}),
        (_('Статусы'), {
            'fields': ('is_pre_registered', 'is_verified', 'has_admin_access'),
            'description': _('Статусы регистрации и доступа')
        }),
        (_('Системные поля Django'), {
            'fields': ('is_active', 'is_staff', 'is_superuser'),
            'classes': ('collapse',),  # Сворачиваемый раздел
            'description': _('Эти поля синхронизируются автоматически')
        }),
        (_('Разрешения'), {
            'fields': ('groups', 'user_permissions'),
            'classes': ('collapse',),
        }),
        (_('Важные даты'), {
            'fields': ('last_login', 'date_joined'),  # Убрали registration_date - оно auto_now_add=True
            'classes': ('collapse',),
        }),
    )
    
    # Поля при создании нового пользователя (упрощенная форма)
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'personnel_number',  # Обязательно
                'username',          # Обязательно для Django
                'first_name',        # Обязательно по вашим требованиям
                'last_name',         # Обязательно по вашим требованиям
                'role',              # Обязательно по вашим требованиям
                'email',             # Необязательно
                'middle_name',       # Необязательно
                'position',          # Необязательно
                'password1',         # Необязательно - оставить пустым
                'password2',         # Необязательно - оставить пустым
            ),
        }),
    )
    
    # Поля только для чтения (нельзя редактировать)
    readonly_fields = ('registration_date',)
    
    # Отображаемые поля в списке пользователей
    list_display = (
        'personnel_number', 
        'username',
        'get_full_name',
        'email',
        'position',
        'role',
        'is_pre_registered',
        'is_verified',
        'has_admin_access',
        'is_active',
        'is_staff',
        'registration_date'  # Добавили для отображения в списке
    )
    
    # Поля для поиска
    search_fields = ('personnel_number', 'username', 'first_name', 'last_name', 'email')
    
    # Фильтры в правой панели
    list_filter = (
        'is_verified',
        'has_admin_access', 
        'is_pre_registered',
        'is_active',
        'is_staff',
        'role',
        'position'
    )
    
    # Порядок сортировки
    ordering = ('personnel_number',)
    
    # Группировка полей в списке
    list_display_links = ('personnel_number', 'username', 'get_full_name')
    
    # Количество объектов на странице
    list_per_page = 20
    
    # Автоматически заполняем username из personnel_number при создании
    def get_changeform_initial_data(self, request):
        initial = super().get_changeform_initial_data(request)
        # Если создаем нового пользователя, предлагаем username = personnel_number
        if 'personnel_number' in initial and not initial.get('username'):
            initial['username'] = initial['personnel_number']
        return initial

# Регистрируем модель с кастомной админкой
admin.site.register(User, CustomUserAdmin)