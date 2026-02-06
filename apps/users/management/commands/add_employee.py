# apps/users/management/commands/add_employee.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.users.models import EmployeePosition, Role

User = get_user_model()
# Пользовательская команда добавления сотрудника админом БД
class Command(BaseCommand):
    help = 'Добавление сотрудника в систему (первый этап регистрации)'
    
    def add_arguments(self, parser):
        parser.add_argument('personnel_number', type=str, help='Табельный номер')
        parser.add_argument('--first-name', type=str, help='Имя', default='')
        parser.add_argument('--last-name', type=str, help='Фамилия', default='')
        parser.add_argument('--middle-name', type=str, help='Отчество', default='')
        parser.add_argument('--email', type=str, help='Email', default='')
        parser.add_argument('--position', type=str, help='Должность', default='Кредитный специалист')
    
    def handle(self, *args, **kwargs):
        personnel_number = kwargs['personnel_number']
        first_name = kwargs['first_name']
        last_name = kwargs['last_name']
        middle_name = kwargs['middle_name']
        email = kwargs['email']
        position_name = kwargs['position']
        
        # Проверяем существует ли уже пользователь
        if User.objects.filter(personnel_number=personnel_number).exists():
            self.stdout.write(
                self.style.WARNING(f'Сотрудник с табельным номером {personnel_number} уже существует')
            )
            return
        
        # Получаем или создаем должность
        position, created = EmployeePosition.objects.get_or_create(name=position_name)
        if created:
            self.stdout.write(f'Создана новая должность: {position_name}')
        
        # Создаем пользователя без пароля (предварительная регистрация)
        username = f"user_{personnel_number}"  # Генерируем временное имя пользователя
        
        user = User.objects.create(
            username=username,
            personnel_number=personnel_number,
            first_name=first_name,
            last_name=last_name,
            middle_name=middle_name,
            email=email,
            position=position,
            is_pre_registered=True,  # Флаг предварительной регистрации
            is_active=True
        )
        
        # Устанавливаем пустой пароль
        user.set_unusable_password()
        user.save()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Сотрудник {last_name} {first_name} (таб. №{personnel_number}) успешно добавлен в систему.\n'
                f'Сотрудник может завершить регистрацию по ссылке: /users/registration/'
            )
        )