# apps/users/tests.py
from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.users.models import Role

User = get_user_model()


class MinimalUserTests(TestCase):
    
    def setUp(self):
        self.role = Role.objects.create(name='Кредитный менеджер')
        self.user = User.objects.create_user(
            username='test@example.com',
            email='test@example.com',
            password='ValidPass123!',
            role=self.role,
            personnel_number='123456',  
            is_pre_registered=False,
            is_verified=True
        )
    
    def test_user_creation(self):
        user = User.objects.create_user(
            username='new@example.com',
            email='new@example.com',
            password='Pass123!',
            role=self.role,
            personnel_number='654321', 
            is_pre_registered=False,
            is_verified=True
        )
        self.assertEqual(user.username, 'new@example.com')
        self.assertTrue(user.check_password('Pass123!'))
    
    def test_password_hashing(self):
        user = User.objects.get(username='test@example.com')
        self.assertNotEqual(user.password, 'ValidPass123!')
        self.assertTrue(user.password.startswith('pbkdf2_sha256$'))
    
    def test_role_assignment(self):
        self.assertEqual(self.user.role.name, 'Кредитный менеджер')
    
    def test_user_string_representation(self):
        self.assertIsNotNone(str(self.user))