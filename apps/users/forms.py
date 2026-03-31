# apps/users/forms.py
from django import forms
from django.contrib.auth.forms import PasswordChangeForm
from django.core.exceptions import ValidationError
from .models import User, EmployeePosition
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.forms import AuthenticationForm
import re


class EmailAuthenticationForm(AuthenticationForm):
    """Форма аутентификации с email как username"""
    
    username = forms.CharField(
        label="Email или табельный номер",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите email или табельный номер',
            'autofocus': True
        })
    )
    
    password = forms.CharField(
        label="Пароль",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите пароль'
        })
    )
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        # Для email приводим к нижнему регистру
        if '@' in username:
            return username.lower()
        return username

class CustomAuthenticationForm(AuthenticationForm):
    def confirm_login_allowed(self, user):
        """Разрешаем вход даже неактивным пользователям"""
        # Полностью убираем проверку is_active
        # Вместо этого проверяем нашу логику
        if not user.has_usable_password():
            raise ValidationError(
                'У вас не установлен пароль. Завершите регистрацию.',
                code='no_password',
            )

class PersonnelNumberForm(forms.Form):
    """Форма для ввода табельного номера админом БД"""
    personnel_number = forms.CharField(
        label="Табельный номер",
        max_length=16,
        widget=forms.TextInput(attrs={ #attrs - словарь с html-атрибутами, которые будут добавлены в тег
            'placeholder': 'Введите ваш табельный номер',
            'class': 'form-control',
            'oninput': 'normalizePersonnelNumber()' #Каждый раз, когда пользователь вводит или удаляет символ, будет запускаться функция
        })
    )
    #серверная валидация табельного
    def clean_personnel_number(self):
        """Очистка табельного номера"""
        personnel_number = self.cleaned_data['personnel_number']
        personnel_number = re.sub(r'\D', '', personnel_number)
        #еслм после очистки пустая строка, то ошибка
        if not personnel_number:
            raise ValidationError('Введите табельный номер')
        return personnel_number


class RegistrationForm(forms.Form):
    """Упрощенная форма завершения регистрации - только пароль"""
    
    password1 = forms.CharField(
        label="Пароль",
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Не менее 8 символов',
            'class': 'form-control',
            'oninput': 'validatePassword()'
        })
    )
    password2 = forms.CharField(
        label="Подтверждение пароля",
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Повторите пароль',
            'class': 'form-control',
            'oninput': 'checkPasswordMatch()'
        })
    )
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
    
    def clean_password1(self):
        password = self.cleaned_data.get('password1')
        if password:
            password_pattern = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[~!?@#$%^&*_\-+()\[\]{}><\/\\|"\'.:,;])[^\s]{8,}$'
            if not re.match(password_pattern, password):
                raise ValidationError(
                    'Пароль должен содержать минимум 8 символов, включать латинские буквы '
                    'в разных регистрах, цифру и специальный символ'
                )
        return password
    
    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        
        if password1 and password2 and password1 != password2:
            raise ValidationError({'password2': 'Пароли не совпадают'})
        
        return cleaned_data
    
    def save(self):
        """Установление пароля и завершение регистрации"""
        if not self.user:
            raise ValidationError('Пользователь не найден')
        
        self.user.set_password(self.cleaned_data['password1'])
        self.user.is_pre_registered = False
        self.user.is_verified = True
        self.user.save()
        
        return self.user

# кастомная смена пароля с его валидацией   
class CustomPasswordChangeForm(PasswordChangeForm):
    def clean_new_password1(self):
        password = self.cleaned_data.get('new_password1')
        if password:
            password_pattern = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[~!?@#$%^&*_\-+()\[\]{}><\/\\|"\'.:,;])[^\s]{8,}$'
            if not re.match(password_pattern, password):
                raise ValidationError(
                    'Пароль должен содержать минимум 8 символов, включать латинские буквы '
                    'в разных регистрах, цифру и специальный символ'
                )
            # пароль не должен совпадать со старым
            old_password = self.cleaned_data.get('old_password')
            if old_password and password == old_password:
                raise ValidationError('Новый пароль должен отличаться от старого')
        return password
    
    def clean(self):
        cleaned_data = super().clean()
        # проверка совпадения новых паролей
        new_password1 = cleaned_data.get('new_password1')
        new_password2 = cleaned_data.get('new_password2')
        if new_password1 and new_password2 and new_password1 != new_password2:
            raise ValidationError({'new_password2': 'Новые пароли не совпадают'})
        return cleaned_data