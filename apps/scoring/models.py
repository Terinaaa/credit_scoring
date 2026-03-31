# apps/scoring/models.py
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class EmploymentType(models.Model):
    id = models.AutoField(primary_key=True)
    """Тип занятости"""
    type = models.CharField(max_length=50, verbose_name='Тип занятости')
    description = models.TextField(blank=True, verbose_name='Описание')
    
    class Meta:
        verbose_name = 'Тип занятости'
        verbose_name_plural = 'Типы занятости'
    
    def __str__(self):
        return self.type

class ApplicationStatus(models.Model):
    id = models.AutoField(primary_key=True)
    """Статус заявки"""
    type = models.CharField(max_length=50, verbose_name='Статус')
    description = models.TextField(blank=True, verbose_name='Описание')
    
    class Meta:
        verbose_name = 'Статус заявки'
        verbose_name_plural = 'Статусы заявок'
    
    def __str__(self):
        return self.type

class SystemDecision(models.Model):
    id = models.AutoField(primary_key=True)
    """Решение системы"""
    decision = models.CharField(max_length=50, verbose_name='Решение')
    description = models.TextField(blank=True, verbose_name='Описание')
    
    class Meta:
        verbose_name = 'Решение системы'
        verbose_name_plural = 'Решения системы'
    
    def __str__(self):
        return self.decision

class RiskCategory(models.Model):
    """Категория риска (1-5)"""
    category = models.IntegerField(
        primary_key=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name='Категория'
    )
    description = models.TextField(verbose_name='Описание')
    
    class Meta:
        verbose_name = 'Категория риска'
        verbose_name_plural = 'Категории риска'
    
    def __str__(self):
        return f"{self.category} - {self.description}"

class ScoringResult(models.Model):
    id = models.AutoField(primary_key=True)
    """Результат скоринговой оценки"""
    user = models.ForeignKey(
        'users.User', 
        on_delete=models.SET_NULL, 
        null=True, 
        verbose_name='Менеджер'
    )
    client = models.ForeignKey(
        'clients.Client',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Клиент'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата оценки')
    input_data = models.JSONField(verbose_name='Входные данные')
    probability = models.FloatField(verbose_name='Вероятность дефолта')
    prediction_class = models.IntegerField(verbose_name='Класс (0 - хороший, 1 - дефолт)')
    recommendation = models.CharField(max_length=20, verbose_name='Рекомендация')
    score = models.IntegerField(null=True, blank=True, verbose_name='Скоринговый балл')
    top_factors = models.JSONField(null=True, blank=True, verbose_name='Ключевые факторы')

    class Meta:
        verbose_name = 'Результат скоринга'
        verbose_name_plural = 'Результаты скоринга'
        ordering = ['-created_at']

    def __str__(self):
        return f'Скоринг #{self.id} от {self.created_at.strftime("%d.%m.%Y")}'