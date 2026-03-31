# apps/users/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models

# должности сотрудников банка
class EmployeePosition(models.Model):
    name = models.CharField(max_length=50, verbose_name="Название должности")
    # класс Meta содержит метаданные модели
    class Meta:
        verbose_name = "Должность" # название модели в админке
        verbose_name_plural = "Должности"
    # магический метод для строкового представления объекта
    def __str__(self):
        # при преобразовании объекта в строку возвращается название должности
        return self.name

# роли пользователей в системе
class Role(models.Model):
    # константа с вариантами ролей, элементы - кортежи
    ROLE_CHOICES = [
        ('credit_manager', 'Кредитный менеджер'),
        ('manager', 'Руководитель'),
        ('db_admin', 'Администратор базы данных'),
        ('system_admin', 'Системный администратор'),
    ]
    # поле с предопределенными вариантами выбора, значение в таблице уникально
    name = models.CharField(max_length=50, choices=ROLE_CHOICES, unique=True)
    # поле описания роли (может быть пустым)
    description = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "Роль"
        verbose_name_plural = "Роли"
    
    def __str__(self):
        # get_name_display() - встроенный метод Django для полей с choices
        # автоматически преобразует 'credit_manager' в 'Кредитный менеджер'
        return self.get_name_display()

# пользователь
# наследование от базового класса модели пользователя 
class User(AbstractUser):
    email = models.EmailField(
        unique=True,
        blank=False,
        null=False,
        verbose_name="Электронная почта"
    )
    
    # новое поле: доступ к админке Django
    has_admin_access = models.BooleanField(
        default=False,  # по умолчанию нет доступа
        verbose_name="Доступ к админке",
        help_text="Определяет, имеет ли пользователь доступ к административному разделу."
    )
    
    # новое поле: статус верификации пользователя
    is_verified = models.BooleanField(
        default=False,  # по умолчанию не верифицирован
        verbose_name="Верифицирован",
        help_text="Пользователь завершил регистрацию и верифицирован администратором"
    )
    
    # табельный номер
    personnel_number = models.CharField(
        max_length=10, 
        unique=True, # уникальное значение для каждого пользователя
        verbose_name="Табельный номер"
    )
    
    # должность сотрудника
    position = models.ForeignKey(
        EmployeePosition,  # связь с моделью EmployeePosition
        on_delete=models.SET_NULL, # при удалении должности из справочника поле становится null
        null=True, # может быть null в БД
        blank=True,
        verbose_name="Должность"
    )
    
    # роль пользователя в системе
    role = models.ForeignKey(
        Role,  # связь с моделью Role
        on_delete=models.PROTECT, # роль нельзя удалить, если она назначена хотя бы одному пользователю
        null=True, 
        blank=True,
        verbose_name="Роль"
    )
    
    # отчество пользователя
    middle_name = models.CharField(
        max_length=50, 
        blank=True, 
        verbose_name="Отчество"
    )
    
    # дата регистрации пользователя
    registration_date = models.DateTimeField(
        auto_now_add=True, # по умолчанию текущие дата и время при создании объекта (при первой записи)
        verbose_name="Дата регистрации"
    )
    
    # флаг предварительной регистрации
    is_pre_registered = models.BooleanField(
        default=True, # значение по умолчанию при создании объекта
        verbose_name="Предварительная регистрация",
        help_text="Сотрудник добавлен администратором, но еще не завершил регистрацию"
    )
    
    # класс метаданных для модели User
    class Meta:
        verbose_name = "Сотрудник"
        verbose_name_plural = "Сотрудники"
    
    # переопределение метода из AbstractUser
    # возврат полного имени с отчеством
    def get_full_name(self):
        # имя и фамилия
        full_name = f"{self.last_name} {self.first_name}"
        # отчество при наличии        
        if self.middle_name:
            full_name += f" {self.middle_name}"
        return full_name.strip()
    
    # строковое представление пользователя.
    # возвращает "ФИО (табельный номер)"
    def __str__(self):
        return f"{self.get_full_name()} ({self.personnel_number})"
    
    # проверка завершения регистрации сотрудником
    # регистрация считается завершенной, если:
    # 1) is_pre_registered = False (администратор подтвердил)
    # 2) Установлен пароль (has_usable_password() возвращает True)
    def has_completed_registration(self):
        return not self.is_pre_registered and self.has_usable_password()
    
    # переопределение метода save
    # автоматическая синхронизация бизнес-логики с полями Django
    def save(self, *args, **kwargs):
        # синхронизируем is_verified с is_pre_registered
        # пользователь верифицирован, если не в предварительной регистрации
        self.is_verified = not self.is_pre_registered
        
        # синхронизируем has_admin_access с ролью пользователя
        # доступ к админке только для административных ролей
        if self.role:
            self.has_admin_access = self.role.name in ['system_admin', 'db_admin']
        else:
            self.has_admin_access = False
        
        # также обновляем стандартные поля Django для обратной совместимости
        # это нужно для корректной работы встроенных механизмов Django
        self.is_active = True  # стандартное поле активности
        self.is_staff = self.has_admin_access  # стандартное поле доступа к админке
        
        # вызов родительского метода для сохранения
        # super() обеспечивает вызов метода из класса-предка (AbstractUser)
        super().save(*args, **kwargs)
    
    USERNAME_FIELD = 'email'  # ← Меняем с 'username' на 'email'
    REQUIRED_FIELDS = ['username', 'personnel_number', 'first_name', 'last_name']
    # свойство (property) - метод, который ведет себя как атрибут
    # вычисляемое свойство для обратной совместимости со старым кодом
    @property
    def is_staff_property(self):
        # возвращает True только для административных ролей.
        # не сохраняется в базу данных
        if hasattr(self, 'role') and self.role:
            return self.role.name in ['system_admin', 'db_admin']
        return False
    
    @property
    def is_active_property(self):
        # активен, если не в предварительной регистрации И имеет пароль
        if hasattr(self, 'is_pre_registered'):
            return not self.is_pre_registered and self.has_usable_password()
        return True
    
    # дополнительные свойства для удобства работы с новыми полями
    @property
    def can_access_admin(self):
        # синоним для has_admin_access для более читаемого кода
        return self.has_admin_access
    
    @property
    def is_fully_registered(self):
        # синоним для is_verified, но с более понятным именем
        return self.is_verified