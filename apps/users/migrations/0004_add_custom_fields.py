# apps/users/migrations/000X_add_custom_fields.py
from django.db import migrations, models

def migrate_data_forward(apps, schema_editor):
    """
    Перенос данных из старых полей в новые при применении миграции
    """
    User = apps.get_model('users', 'User')
    
    for user in User.objects.all():
        # Копируем значение is_staff в has_admin_access
        user.has_admin_access = user.is_staff
        
        # Определяем is_verified на основе is_pre_registered
        user.is_verified = not user.is_pre_registered
        
        # Сохраняем только новые поля, чтобы избежать рекурсии
        user.save(update_fields=['has_admin_access', 'is_verified'])
        print(f"Мигрирован пользователь {user.personnel_number}: "
              f"has_admin_access={user.has_admin_access}, "
              f"is_verified={user.is_verified}")

def migrate_data_backward(apps, schema_editor):
    """
    Возвращаем данные из новых полей в старые при откате миграции
    """
    User = apps.get_model('users', 'User')
    
    for user in User.objects.all():
        # Восстанавливаем is_staff из has_admin_access
        user.is_staff = user.has_admin_access
        
        # Восстанавливаем is_active из is_verified
        user.is_active = user.is_verified
        
        user.save(update_fields=['is_staff', 'is_active'])
        print(f"Откат пользователя {user.personnel_number}")

class Migration(migrations.Migration):
    # Найдите номер последней миграции:
    # ls apps/users/migrations/000*.py
    dependencies = [
        ('users', '0003_user_is_pre_registered_alter_user_email'),  # ЗАМЕНИТЕ X на номер предыдущей миграции
    ]

    operations = [
        # Добавляем новые поля в базу данных
        migrations.AddField(
            model_name='user',
            name='has_admin_access',
            field=models.BooleanField(
                default=False,
                help_text='Определяет, имеет ли пользователь доступ к административному разделу.',
                verbose_name='Доступ к админке'
            ),
        ),
        migrations.AddField(
            model_name='user',
            name='is_verified',
            field=models.BooleanField(
                default=False,
                help_text='Пользователь завершил регистрацию и верифицирован администратором',
                verbose_name='Верифицирован'
            ),
        ),
        
        # Запускаем функцию переноса данных
        migrations.RunPython(
            migrate_data_forward,    # функция для применения миграции
            migrate_data_backward,   # функция для отката миграции
        ),
    ]