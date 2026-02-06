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


class RegistrationForm(forms.ModelForm):
    """Форма завершения регистрации сотрудником"""
    email = forms.EmailField(
        label="Электронная почта",
        widget=forms.EmailInput(attrs={
            'placeholder': 'example@mail.ru',
            'class': 'form-control'
        })
    )
    last_name = forms.CharField(
        label="Фамилия",
        widget=forms.TextInput(attrs={
            'placeholder': 'Иванов',
            'class': 'form-control',
            'oninput': "validateName(this)"
        })
    )
    first_name = forms.CharField(
        label="Имя",
        widget=forms.TextInput(attrs={
            'placeholder': 'Иван',
            'class': 'form-control',
            'oninput': "validateName(this)"
        })
    )
    middle_name = forms.CharField(
        label="Отчество",
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Иванович',
            'class': 'form-control',
            'oninput': "validateName(this)"
        })
    )
    position = forms.ModelChoiceField(
        label="Должность",
        queryset=EmployeePosition.objects.all(),
        empty_label="Выберите должность",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    password1 = forms.CharField(
        label="Пароль",
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Не менее 8 символов. Минимум одна строчная буква, одна прописная, цифра и символ',
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
    # связка формы с молелью базы данных User, определение отражаемых и обрабатываемых полей
    class Meta:
        model = User
        fields = [
            'email', 'last_name', 'first_name', 
            'middle_name', 'position', 'password1', 'password2'
        ]
    # ToDo: РАЗОБРАТЬСЯ С ЭТИМ 
    def __init__(self, *args, **kwargs):
        self.personnel_number = kwargs.pop('personnel_number', None)
        super().__init__(*args, **kwargs)
    
    def clean_personnel_number(self):
        """Проверка табельного номера"""
        if not self.personnel_number:
            raise ValidationError('Табельный номер не указан')
        return self.personnel_number
    
    def clean_email(self):
        """Валидация email"""
        # приведение к нижнему регистру
        email = self.cleaned_data['email'].lower()
        
        # проверка использования почты другим пользователем
        if User.objects.filter(email=email).exclude(personnel_number=self.personnel_number).exists():
            raise ValidationError('Указанный адрес уже используется другим сотрудником')
        
        return email
    # валидация пароля
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
    # проверка совпадения паролей
    def clean(self):
        cleaned_data = super().clean() # вызов родительского метода
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        
        if password1 and password2 and password1 != password2:
            # при несовпадении ошибка на второй введенный пароль
            raise ValidationError({'password2': 'Пароли не совпадают'})
        
        return cleaned_data
    # сохранение (обновление) данных пользователя после регистрации
    def save(self, commit=True):
        # поиск пользователя по табельному номеру
        try:
            user = User.objects.get(personnel_number=self.personnel_number)
        except User.DoesNotExist:
            raise ValidationError('Сотрудник с таким табельным номером не найден')
        
        # проверка завершения регистрации
        if not user.is_pre_registered:
            raise ValidationError('Регистрация для данного сотрудника уже завершена')
        
        # обновление данных пользователя
        user.email = self.cleaned_data['email']
        user.last_name = self.cleaned_data['last_name']
        user.first_name = self.cleaned_data['first_name']
        user.middle_name = self.cleaned_data['middle_name']
        user.position = self.cleaned_data['position']
        user.set_password(self.cleaned_data['password1']) # хэширование пароля
        user.is_pre_registered = False  # изменение флага завершения регистрации
        
        # Устанавливаем роль по умолчанию (кредитный менеджер), если не установлена
        if not user.role:
            from .models import Role
            default_role, created = Role.objects.get_or_create(
                name='credit_manager',
                defaults={'description': 'Кредитный менеджер'}
            )
            user.role = default_role
        
        if commit:
            user.save()
        
        return user

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