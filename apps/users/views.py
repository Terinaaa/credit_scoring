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
    # если пользователь авторизован, редирект на главную
    if request.user.is_authenticated:
        return redirect('index')
   # проверка, есть ли в сессии табельный номер. Если пользователь попытается зайти на эту страницу напрямую (через URL),
   # его выкинет обратно на первый шаг
    personnel_number = request.session.get('registration_personnel_number')
    if not personnel_number:
        messages.error(request, 'Сначала введите табельный номер')
        return redirect('registration_start')
    
    # проверка наличия сотрудника и незавершенной регистрации
    try:
        user = User.objects.get(personnel_number=personnel_number)
        if not user.is_pre_registered:
            messages.error(request, 'Регистрация для данного пользователя уже завершена')
            return redirect('login')
    except User.DoesNotExist:
        messages.error(request, 'Сотрудник не найден')
        return redirect('registration_start')
    # получение списка должностей из БД для выпадающего списка
    positions = EmployeePosition.objects.all().order_by('name')
    
    if request.method == 'POST':
        # создание формы и передача в нее табельного
        form = RegistrationForm(request.POST, personnel_number=personnel_number)
        if form.is_valid():
            # обновление данных пользователя в БД
            user = form.save()
            # очистка сессии
            if 'registration_personnel_number' in request.session:
                del request.session['registration_personnel_number']
            # автоматическая аутентификация после регистрации
            login(request, user)
            # сообщение об успешном завершении регистрации
            messages.success(request, 
                'Регистрация прошла успешно! Добро пожаловать в систему.')
            return redirect('index')
    else:
        # предзаполнение формы, если есть некоторые данные пользователя в БД
        initial_data = {}
        if user.first_name:
            initial_data['first_name'] = user.first_name
        if user.last_name:
            initial_data['last_name'] = user.last_name
        if user.middle_name:
            initial_data['middle_name'] = user.middle_name
        if user.email:
            initial_data['email'] = user.email
        if user.position:
            initial_data['position'] = user.position
        
        form = RegistrationForm(initial=initial_data, personnel_number=personnel_number)
    
    return render(request, 'users/registration_complete.html', {
        'form': form,
        'positions': positions,
        'personnel_number': personnel_number
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