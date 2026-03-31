# apps/users/db_admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User
from django import forms
from django.contrib.auth.forms import UserCreationForm

class DBCustomUserCreationForm(UserCreationForm):
    """Форма создания пользователя для администратора БД"""
    
    class Meta:
        model = User
        fields = ('personnel_number', 'username', 'email', 'first_name', 
                  'last_name', 'middle_name', 'position', 'role')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Делаем пароль необязательным
        self.fields['password1'].required = False
        self.fields['password2'].required = False
        self.fields['password1'].help_text = _('Оставьте пустым - пользователь установит пароль при регистрации')
        self.fields['password2'].help_text = _('Оставьте пустым')
        
        # Делаем username необязательным, будет заполнен автоматически
        self.fields['username'].required = False
        self.fields['username'].help_text = _('Оставьте пустым - будет создан автоматически')
        
        # Все поля ФИО и email обязательны
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        self.fields['email'].required = True
        self.fields['position'].required = True
        self.fields['role'].required = True
    
    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 or password2:
            return super().clean_password2()
        return password2
    
    def save(self, commit=True):
        user = super().save(commit=False)
        
        # Если пароль не введен, устанавливаем непригодный пароль
        if not self.cleaned_data["password1"]:
            user.set_unusable_password()
        
        # Если username не указан, создаем из personnel_number
        if not user.username:
            user.username = user.personnel_number
        
        # Устанавливаем флаг предварительной регистрации
        user.is_pre_registered = True
        
        if commit:
            user.save()
        return user

class DBUserAdmin(UserAdmin):
    """Админка для администратора БД - управление пользователями и данными"""
    add_form = DBCustomUserCreationForm
    
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
            'classes': ('collapse',),
        }),
        (_('Разрешения'), {
            'fields': ('groups', 'user_permissions'),
            'classes': ('collapse',),
        }),
        (_('Важные даты'), {
            'fields': ('last_login', 'date_joined'),
            'classes': ('collapse',),
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'personnel_number',
                'email',
                'first_name',
                'last_name',
                'middle_name',
                'position',
                'role',
                'username',  # опционально
                'password1',
                'password2',
            ),
        }),
    )
    
    readonly_fields = ('registration_date',)
    
    list_display = (
        'personnel_number',
        'get_full_name',
        'email',
        'position',
        'role',
        'is_pre_registered',
        'is_verified',
    )
    
    search_fields = ('personnel_number', 'email', 'first_name', 'last_name')
    
    list_filter = ('is_pre_registered', 'is_verified', 'role', 'position')
    
    ordering = ('personnel_number',)
    
    def get_changeform_initial_data(self, request):
        initial = super().get_changeform_initial_data(request)
        return initial