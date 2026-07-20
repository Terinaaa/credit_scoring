# apps/clients/tests.py
from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.clients.models import Client
from apps.users.models import Role

User = get_user_model()

class SQLInjectionTest(TestCase):
    
    def setUp(self):
        role = Role.objects.create(name='Кредитный менеджер')
        self.user = User.objects.create_user(
            username='test@example.com',
            email='test@example.com',
            password='Pass123!',
            role=role,
            is_pre_registered=False,
            is_verified=True
        )
        # Создание тестового клиента
        Client.objects.create(
            doc_series='1234',
            doc_number='567890',
            last_name='Иванов',
            first_name='Иван',
            birth_date='1990-01-01',
            email='ivan@example.com',
            phone_num='+79991234567',
            created_by=self.user
        )
    
    def test_sql_injection_does_not_break_system(self):

        self.client.login(username='test@example.com', password='Pass123!')
        
        # Попытка инъекции в поле поиска
        response = self.client.get('/clients/', {
            'doc_series': "1234' OR '1'='1",
            'doc_number': ''
        })
        
        # Проверка: страница загрузилась (статус 200)
        # Если будет редирект из-за отсутствия logout,тест упадёт
        self.assertEqual(response.status_code, 200)
        
        # Проверка (в ответе нет SQL-ошибок)
        content = response.content.decode()
        self.assertNotIn('SQL', content)
        self.assertNotIn('syntax error', content)
        self.assertNotIn('ORA-', content)
        self.assertNotIn('MySQL', content)