from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout,update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import RegistrationForm, PersonnelNumberForm, EmailAuthenticationForm
from .models import User, EmployeePosition
from .forms import CustomPasswordChangeForm


# главная страница
def index_view(request):
    return render(request, 'index.html')

# вход в систему
def login_view(request):
    # если пользователь авторизован, редирект на главную
    if request.user.is_authenticated:
        return redirect('index')
    
    # срабатывает, когда пользователь нажал кнопку «Войти» и отправил свои данные
    if request.method == 'POST':
        # создание объекта формы и заполнение его данными от пользователя
        form = EmailAuthenticationForm(request, data=request.POST)
        form.error_messages
        # проверка полей
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            # проверка существования пользователя с таким паролем в БД
            user = authenticate(username=username, password=password)
            # если такой пользователь существует
            if user is not None:
                # создлание сессии
                login(request, user)
                # уведомление об успешном входе в систему
                messages.success(request, 'Вход выполнен успешно')
                # редирект на главную
                return redirect('index')
            else:
                messages.error(request, 'Неверный логин или пароль')
        else:
            user = authenticate(username=form.cleaned_data.get('username'), password=form.cleaned_data.get('password'))
            if user is not None:
                print("not None")
            messages.error(request, 'Неверный логин или пароль')
    # если просто открыта форма входа, то отображение пустой формы
    else:
        form = EmailAuthenticationForm()
    
    return render(request, 'users/login.html', {'form': form})

# двухэтапная регистрация
# первый этап регистрации
def registration_start_view(request):
    # если пользователь авторизован, редирект на главную
    if request.user.is_authenticated:
        return redirect('index')
    
    if request.method == 'POST':
        form = PersonnelNumberForm(request.POST)
        if form.is_valid():
            personnel_number = form.cleaned_data['personnel_number']
            
            # проверка наличия сотрудника с таким номером в БД
            try:
                user = User.objects.get(personnel_number=personnel_number)
                
                # проверка статуса регистрации
                # если пользователь уже завершил регистрацию после внесения табельного в БД, то вывод сообщения об этом
                if not user.is_pre_registered:
                    messages.error(request, 
                        'Регистрация для данного сотрудника уже завершена. '
                        'Если вы забыли пароль, обратитесь к администратору.')
                    return redirect('login')
                
                # сохранение табельного номера в сессии и переход к следующему шагу регистрации
                request.session['registration_personnel_number'] = personnel_number
                return redirect('registration_complete')
            # если такого табельного нет в БД, вывод сообщения    
            except User.DoesNotExist:
                messages.error(request, 
                    'Сотрудник с таким табельным номером не найден. '
                    'Обратитесь к администратору для добавления в систему.')
    else:
        form = PersonnelNumberForm()
    
    return render(request, 'users/registration_start.html', {'form': form})

# второй шаг регистрации
def registration_complete_view(request):
    if request.user.is_authenticated:
        return redirect('index')
    
    personnel_number = request.session.get('registration_personnel_number')
    if not personnel_number:
        messages.error(request, 'Сначала введите табельный номер')
        return redirect('registration_start')
    
    try:
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
            form.save()
            # Очистка сессии
            if 'registration_personnel_number' in request.session:
                del request.session['registration_personnel_number']
            
            # Автоматический вход
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, 'Регистрация успешно завершена!')
            return redirect('index')
    else:
        form = RegistrationForm(user=user)
    
    # Показываем пользователю его данные для подтверждения
    return render(request, 'users/registration_complete.html', {
        'form': form,
        'user_data': user  # передаем данные пользователя для отображения
    })
# декоратор для проверки аутентификации
@login_required
# выход из системы
def logout_view(request):
    logout(request) # стандартная функция django
    # сообщение об успешном выходе
    messages.success(request, 'Вы успешно вышли из системы')
    # редирект на главную
    return redirect('index')
# декоратор для проверки аутентификации
@login_required
# простое отображение страницы профиля
def personal_account_view(request):
    return render(request, 'users/personal_account.html', {
        'user': request.user
    })

def personal_account_view(request):
    return render(request, 'users/personal_account.html')

@login_required
def change_password_view(request):
    if request.method == 'POST':
        form = CustomPasswordChangeForm(request.user, request.POST) # кастомная форма смены пароля
        if form.is_valid():
            user = form.save() # сохранение нового пароля в БД
            # обновление сессии, чтобы пользователь не разлогинился
            update_session_auth_hash(request, user)
            messages.success(request, 'Пароль успешно изменен!')
            return redirect('personal_account')
    else:
        form = CustomPasswordChangeForm(request.user)
    
    return render(request, 'users/change_password.html', {'form': form})