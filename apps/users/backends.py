# apps/users/backends.py
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

class EmailOrUsernameBackend(ModelBackend):
    """Бэкенд для аутентификации по email или username"""
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        
        if username is None:
            username = kwargs.get(UserModel.USERNAME_FIELD)
        
        # Приводим к нижнему регистру если это email
        identifier = username.lower() if '@' in username else username
        
        try:
            # Ищем пользователя по email (основной способ)
            # или по username/табельному для обратной совместимости
            user = UserModel.objects.get(
                Q(email__iexact=identifier) | 
                Q(username=identifier) |
                Q(personnel_number=identifier)
            )
        except UserModel.DoesNotExist:
            return None
        
        # Проверяем пароль
        if user.check_password(password):
            return user
        
        return None