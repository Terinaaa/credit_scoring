# apps/credit/tests.py
from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.clients.models import Client, ClientData
from apps.credit.models import CreditApplication
from apps.users.models import Role
from apps.scoring.models import ApplicationStatus

User = get_user_model()


class MinimalCreditTests(TestCase):
    
    def setUp(self):
        # Создание роли
        self.role = Role.objects.create(name='Кредитный менеджер')
        
        # Создание пользователя
        self.user = User.objects.create_user(
            username='test@example.com',
            email='test@example.com',
            password='Pass123!',
            role=self.role,
            personnel_number='123456',
            is_pre_registered=False,
            is_verified=True
        )
        
        # Создание клиента
        self.client_obj = Client.objects.create(
            doc_series='1234',
            doc_number='567890',
            last_name='Иванов',
            first_name='Иван',
            birth_date='1990-01-01',
            email='ivan@example.com',
            phone_num='+79991234567',
            created_by=self.user
        )
        
        # Создание финансовых данных клиента
        self.client_data = ClientData.objects.create(
            client=self.client_obj,
            loan_amnt=100000,
            installment=5000,
            annual_inc=600000,
            dti=25,
            home_ownership='RENT',
            emp_length=5
        )
        
        # Создание статуса заявки
        self.status = ApplicationStatus.objects.create(
            type='Новая',
            description='Только создана'
        )
    
    def test_credit_application_creation(self):
        application = CreditApplication.objects.create(
            client=self.client_obj,
            client_data=self.client_data,
            loan_amount=100000,
            loan_term_months=12,
            status=self.status,
            created_by=self.user
        )
        
        # Проверка: заявка создана
        self.assertIsNotNone(application.id)
        
        # Проверка: сумма кредита совпадает
        self.assertEqual(application.loan_amount, 100000)
        
        # Проверка: срок кредита совпадает
        self.assertEqual(application.loan_term_months, 12)
        
        # Проверка: клиент привязан правильно
        self.assertEqual(application.client.last_name, 'Иванов')
        
        # Проверка: номер заявки сгенерирован автоматически
        self.assertIsNotNone(application.app_num)
        self.assertGreater(len(application.app_num), 0)
    
    def test_application_str_representation(self):
        application = CreditApplication.objects.create(
            client=self.client_obj,
            client_data=self.client_data,
            loan_amount=50000,
            loan_term_months=6,
            status=self.status,
            created_by=self.user
        )
        
        str_value = str(application)
        self.assertIn(application.app_num, str_value)
        self.assertIn('Иванов', str_value)
    
    def test_application_default_status(self):
        application = CreditApplication.objects.create(
            client=self.client_obj,
            client_data=self.client_data,
            loan_amount=30000,
            loan_term_months=24,
            status=self.status,
            created_by=self.user
        )
        
        self.assertEqual(application.status.type, 'Новая')