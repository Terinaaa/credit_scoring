# apps/clients/models.py
from django.db import models
from django.core.validators import RegexValidator, EmailValidator, MinValueValidator, MaxValueValidator
from django.utils import timezone

class Client(models.Model):
    """Модель клиента банка"""
    id = models.AutoField(primary_key=True)
    
    # Документы
    doc_series = models.CharField(
        max_length=4,
        validators=[RegexValidator(r'^\d{4}$', 'Серия паспорта должна состоять из 4 цифр')],
        verbose_name='Серия паспорта'
    )
    doc_number = models.CharField(
        max_length=6,
        validators=[RegexValidator(r'^\d{6}$', 'Номер паспорта должен состоять из 6 цифр')],
        verbose_name='Номер паспорта'
    )
    
    # ФИО
    first_name = models.CharField(max_length=100, verbose_name='Имя')
    last_name = models.CharField(max_length=100, verbose_name='Фамилия')
    middle_name = models.CharField(max_length=100, blank=True, null=True, verbose_name='Отчество')
    
    # Личные данные
    birth_date = models.DateField(verbose_name='Дата рождения')
    email = models.EmailField(
        max_length=50,
        validators=[EmailValidator()],
        verbose_name='Email'
    )
    phone_num = models.CharField(
        max_length=30,
        validators=[RegexValidator(r'^\+?1?\d{9,15}$', 'Некорректный номер телефона')],
        verbose_name='Телефон'
    )
    
    # Метаданные
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    created_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_clients',
        verbose_name='Создал'
    )

    class Meta:
        verbose_name = 'Клиент'
        verbose_name_plural = 'Клиенты'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['doc_series', 'doc_number']),
            models.Index(fields=['last_name', 'first_name']),
            models.Index(fields=['phone_num']),
            models.Index(fields=['email']),
        ]
        unique_together = ['doc_series', 'doc_number']

    def __str__(self):
        return f"{self.last_name} {self.first_name} {self.middle_name or ''} ({self.doc_series} {self.doc_number})"

    def get_full_name(self):
        """Полное имя клиента"""
        return f"{self.last_name} {self.first_name} {self.middle_name or ''}".strip()

    def get_passport(self):
        """Паспортные данные"""
        return f"{self.doc_series} {self.doc_number}"


class ClientData(models.Model):
    """
    Финансовые данные клиента для кредитного скоринга.
    Содержит все признаки, на которых обучалась модель XGBoost.
    """
    id = models.AutoField(primary_key=True)
    client = models.ForeignKey(
        Client, 
        on_delete=models.CASCADE,
        related_name='financial_data',
        verbose_name='Клиент'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    
    # ==================== 1. Платежеспособность ====================
    loan_amnt = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name='Сумма кредита'
    )
    installment = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name='Ежемесячный платеж'
    )
    annual_inc = models.DecimalField(
        max_digits=12, decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name='Годовой доход'
    )
    dti = models.DecimalField(
        max_digits=5, decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name='Debt-to-Income (DTI, %)'
    )
    
    # ==================== 2. Кредитная дисциплина ====================
    delinq_2yrs = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='Просрочек за 2 года'
    )
    acc_now_delinq = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='Текущих просрочек'
    )
    pub_rec = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='Публичных записей (банкротства и т.д.)'
    )
    pub_rec_bankruptcies = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='Банкротств'
    )
    collections_12_mths_ex_med = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='Взысканий за 12 месяцев (без медицинских)'
    )
    
    # ==================== 3. Кредитная нагрузка ====================
    revol_util = models.DecimalField(
        max_digits=5, decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name='Revolving utilization (%)'
    )
    bc_util = models.DecimalField(
        max_digits=5, decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name='Utilization по банковским картам (%)'
    )
    total_bal_ex_mort = models.DecimalField(
        max_digits=12, decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='Общий баланс без ипотеки'
    )
    total_acc = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='Всего кредитов (исторически)'
    )
    tot_hi_cred_lim = models.DecimalField(
        max_digits=12, decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='Общий кредитный лимит'
    )
    
    # ==================== 4. Стабильность ====================
    emp_length = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(70)],
        verbose_name='Стаж работы (лет)'
    )
    home_ownership = models.CharField(
        max_length=20,
        choices=[
            ('RENT', 'Аренда'),
            ('MORTGAGE', 'Ипотека'),
            ('OWN', 'Собственное'),
            ('OTHER', 'Другое'),
        ],
        verbose_name='Тип жилья'
    )
    earliest_cr_line = models.DateField(
        null=True, 
        blank=True,
        verbose_name='Дата первого кредита'
    )
    
    # ==================== 5. Поведенческий риск ====================
    inq_last_6mths = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='Запросов в БКИ за 6 месяцев'
    )
    mths_since_recent_inq = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='Месяцев с последнего запроса в БКИ'
    )
    percent_bc_gt_75 = models.DecimalField(
        max_digits=5, decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name='% карт с utilization > 75%'
    )
    
    # ==================== Вспомогательные поля (для обратной совместимости) ====================
    # Эти поля оставлены для совместимости, но не используются в модели скоринга
    monthly_income = models.DecimalField(
        max_digits=10, decimal_places=2,
        null=True, blank=True,
        validators=[MinValueValidator(0)],
        verbose_name='Ежемесячный доход'
    )
    additional_income = models.DecimalField(
        max_digits=10, decimal_places=2,
        default=0, null=True, blank=True,
        validators=[MinValueValidator(0)],
        verbose_name='Дополнительный доход'
    )
    employment_type = models.ForeignKey(
        'scoring.EmploymentType',
        on_delete=models.PROTECT,
        null=True, blank=True,
        verbose_name='Тип занятости'
    )
    employment_years = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(0)],
        verbose_name='Стаж работы (лет)'
    )
    has_real_estate = models.BooleanField(default=False, verbose_name='Недвижимость')
    has_car = models.BooleanField(default=False, verbose_name='Автомобиль')
    has_business = models.BooleanField(default=False, verbose_name='Бизнес')
    existing_credits_count = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='Количество действующих кредитов'
    )
    total_monthly_payments = models.DecimalField(
        max_digits=10, decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='Ежемесячные платежи по кредитам'
    )

    class Meta:
        verbose_name = 'Данные клиента'
        verbose_name_plural = 'Данные клиентов'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Данные клиента {self.client.get_full_name()} от {self.created_at.date()}"
    
    def get_total_income(self):
        """Общий доход (для совместимости)"""
        if self.monthly_income:
            return self.monthly_income + (self.additional_income or 0)
        return 0
    
    def get_debt_to_income(self):
        """Показатель долговой нагрузки (DTI) - для совместимости"""
        if self.get_total_income() > 0:
            return (self.total_monthly_payments / self.get_total_income()) * 100
        return self.dti or 0
    
    def get_credit_history_years(self):
        """Возраст кредитной истории в годах"""
        if self.earliest_cr_line:
            current_year = timezone.now().year
            return current_year - self.earliest_cr_line.year
        return 0