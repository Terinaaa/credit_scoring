from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import RegistrationForm, PersonnelNumberForm, EmailAuthenticationForm
from .models import User
from .forms import CustomPasswordChangeForm


def index_view(request):
    """Отображение стартовой страницы системы."""
    return render(request, 'index.html')

def login_view(request):
    """Аутентификация сотрудника по учетным данным."""
    # Проверка текущей сессии: авторизованному пользователю повторный вход не требуется.
    if request.user.is_authenticated:
        return redirect('index')
    
    if request.method == 'POST':
        # Валидация формы входа с проверкой обязательных полей и формата значений.
        form = EmailAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            # Проверка пары логин/пароль через стандартный backend Django.
            user = authenticate(username=username, password=password)
            if user is not None:
                # Создание пользовательской сессии после успешной аутентификации.
                login(request, user)
                messages.success(request, 'Вход выполнен успешно')
                return redirect('index')
        else:
            messages.error(request, 'Неверный логин или пароль')
    # Отображение пустой формы при первом открытии страницы входа.
    else:
        form = EmailAuthenticationForm()
    
    return render(request, 'users/login.html', {'form': form})

def registration_start_view(request):
    """Первый шаг регистрации: проверка табельного номера сотрудника."""
    # Защита от повторной регистрации в активной сессии.
    if request.user.is_authenticated:
        return redirect('index')
    
    if request.method == 'POST':
        form = PersonnelNumberForm(request.POST)
        if form.is_valid():
            personnel_number = form.cleaned_data['personnel_number']
            
            # Поиск сотрудника, предварительно заведенного администратором в систему.
            try:
                user = User.objects.get(personnel_number=personnel_number)
                
                # Контроль этапа регистрации: завершившему регистрацию сотруднику повторный путь закрывается.
                if not user.is_pre_registered:
                    messages.error(request, 
                        'Регистрация для данного сотрудника уже завершена. '
                        'Если вы забыли пароль, обратитесь к администратору.')
                    return redirect('login')
                
                # Сохранение идентификатора шага регистрации в сессии между запросами.
                request.session['registration_personnel_number'] = personnel_number
                return redirect('registration_complete')
            # Обработка сценария отсутствующего сотрудника в реестре.
            except User.DoesNotExist:
                messages.error(request, 
                    'Сотрудник с таким табельным номером не найден. '
                    'Обратитесь к администратору для добавления в систему.')
    else:
        form = PersonnelNumberForm()
    
    return render(request, 'users/registration_start.html', {'form': form})

def registration_complete_view(request):
    """Второй шаг регистрации: создание постоянных учетных данных."""
    if request.user.is_authenticated:
        return redirect('index')
    
    # Извлечение табельного номера из сессии, установленного на первом шаге регистрации.
    personnel_number = request.session.get('registration_personnel_number')
    if not personnel_number:
        messages.error(request, 'Сначала введите табельный номер')
        return redirect('registration_start')
    
    try:
        # Повторная проверка существования сотрудника и статуса предварительной регистрации.
        user = User.objects.get(personnel_number=personnel_number)
        if not user.is_pre_registered:
            messages.error(request, 'Регистрация для данного пользователя уже завершена')
            return redirect('login')
    except User.DoesNotExist:
        messages.error(request, 'Сотрудник не найден')
        return redirect('registration_start')
    
    if request.method == 'POST':
        form = RegistrationForm(request.POST, user=user)
        if form.is_valid():
            # Сохранение персональных данных и пароля пользователя.
            form.save()
            # Очистка временного ключа сессии после завершения регистрационного процесса.
            if 'registration_personnel_number' in request.session:
                del request.session['registration_personnel_number']
            
            # Автоматический вход сразу после регистрации для бесшовного старта работы.
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, 'Регистрация успешно завершена!')
            return redirect('index')
    else:
        form = RegistrationForm(user=user)
    
    # Отображение формы регистрации с уже найденными служебными данными сотрудника.
    return render(request, 'users/registration_complete.html', {
        'form': form,
        'user_data': user
    })

@login_required
def logout_view(request):
    """Завершение пользовательской сессии."""
    logout(request)
    messages.success(request, 'Вы успешно вышли из системы')
    return redirect('index')

@login_required
def personal_account_view(request):
    """Отображение профиля текущего авторизованного сотрудника."""
    return render(request, 'users/personal_account.html')

@login_required
def change_password_view(request):
    """Смена пароля с сохранением текущей сессии пользователя."""
    if request.method == 'POST':
        # Валидация формы смены пароля, включая проверку текущего пароля и сложности нового.
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            # Применение нового пароля в базе данных.
            user = form.save()
            # Обновление hash сессии: защита от принудительного выхода после смены пароля.
            update_session_auth_hash(request, user)
            messages.success(request, 'Пароль успешно изменен!')
            return redirect('personal_account')
    else:
        form = CustomPasswordChangeForm(request.user)
    
    return render(request, 'users/change_password.html', {'form': form})