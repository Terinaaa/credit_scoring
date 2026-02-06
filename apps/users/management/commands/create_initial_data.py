# apps/users/management/commands/create_initial_data.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.users.models import Role, EmployeePosition

class Command(BaseCommand):
    help = 'Создание начальных данных для системы'
    
    def handle(self, *args, **kwargs):
        # Создаем роли
        roles = [
            ('credit_manager', 'Кредитный менеджер'),
            ('manager', 'Руководитель'),
            ('db_admin', 'Администратор базы данных'),
            ('system_admin', 'Системный администратор'),
        ]
        
        for role_code, role_name in roles:
            Role.objects.get_or_create(
                name=role_code,
                defaults={'description': f'Роль {role_name}'}
            )
            self.stdout.write(f'Создана роль: {role_name}')
        
        # Создаем должности
        positions = [
            'Кредитный специалист',
            'Руководитель отдела',
            'Администратор БД',
            'Системный администратор',
            'Аналитик',
        ]
        
        for position_name in positions:
            EmployeePosition.objects.get_or_create(name=position_name)
            self.stdout.write(f'Создана должность: {position_name}')
        
        self.stdout.write(self.style.SUCCESS('Начальные данные созданы!'))