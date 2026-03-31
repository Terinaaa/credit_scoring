# apps/credit/models.py
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.clients.models import Client, ClientData
from apps.scoring.models import ApplicationStatus, SystemDecision, RiskCategory

class CreditApplication(models.Model):
    """Кредитная заявка"""
    id = models.AutoField(primary_key=True)
    # Основная информация
    app_num = models.CharField(
        max_length=20, 
        unique=True,
        verbose_name='Номер заявки'
    )
    client = models.ForeignKey(
        Client,
        on_delete=models.PROTECT,
        related_name='credit_applications',
        verbose_name='Клиент'
    )
    client_data = models.ForeignKey(
        ClientData,
        on_delete=models.PROTECT,
        related_name='applications',
        verbose_name='Данные клиента на момент заявки'
    )
    
    # Параметры кредита
    loan_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(1000)],
        verbose_name='Сумма кредита'
    )
    loan_term_months = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(360)],
        verbose_name='Срок кредита (мес)'
    )
    
    # Результаты скоринга
    scoring_score = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(1000)],
        verbose_name='Скоринговый балл'
    )
    scoring_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Дата скоринга'
    )
    probability_default = models.FloatField(
        null=True,
        blank=True,
        verbose_name='Вероятность дефолта'
    )
    
    # Статусы и решения
    status = models.ForeignKey(
        ApplicationStatus,
        on_delete=models.PROTECT,
        verbose_name='Статус заявки'
    )
    system_decision = models.ForeignKey(
        SystemDecision,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name='Решение системы'
    )
    risk_category = models.ForeignKey(
        RiskCategory,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name='Категория риска'
    )
    
    # Временные метки
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    created_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Создал'
    )
    
    # SHAP факторы
    top_factors = models.JSONField(
        null=True,
        blank=True,
        verbose_name='Ключевые факторы'
    )
    
    class Meta:
        verbose_name = 'Кредитная заявка'
        verbose_name_plural = 'Кредитные заявки'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['client', 'created_at']),
            models.Index(fields=['app_num']),
        ]
    
    def __str__(self):
        return f"Заявка {self.app_num} - {self.client.get_full_name()}"
    
    def save(self, *args, **kwargs):
        if not self.app_num:
            # Генерация номера заявки: ГГГГММДД-XXXX
            from django.utils import timezone
            today = timezone.now().strftime('%Y%m%d')
            last_today = CreditApplication.objects.filter(
                app_num__startswith=today
            ).count()
            self.app_num = f"{today}-{last_today + 1:04d}"
        super().save(*args, **kwargs)