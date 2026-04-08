# apps/credit/forms.py
from django import forms
from django.utils import timezone
from .models import CreditApplication
from apps.clients.models import ClientData
from apps.scoring.models import EmploymentType
from apps.scoring.models import ApplicationStatus


class CreditApplicationForm(forms.ModelForm):
    """Форма создания кредитной заявки (только параметры кредита)"""
    
    class Meta:
        model = CreditApplication
        fields = [
            'loan_amount',
            'loan_term_months',
        ]
        widgets = {
            'loan_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите сумму'
            }),
            'loan_term_months': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите срок в месяцах'
            }),
        }
        labels = {
            'loan_amount': 'Сумма кредита (₽)',
            'loan_term_months': 'Срок кредита (мес)',
        }
    
    def clean_loan_amount(self):
        amount = self.cleaned_data.get('loan_amount')
        if amount is None:
            raise forms.ValidationError('Укажите сумму кредита')
        if amount <= 0:
            raise forms.ValidationError('Сумма кредита должна быть положительной')
        if amount < 1000:
            raise forms.ValidationError('Минимальная сумма кредита - 1 000 ₽')
        if amount > 10000000:
            raise forms.ValidationError('Максимальная сумма кредита - 10 000 000 ₽')
        return amount
    
    def clean_loan_term_months(self):
        term = self.cleaned_data.get('loan_term_months')
        if term is None:
            raise forms.ValidationError('Укажите срок кредита')
        if term <= 0:
            raise forms.ValidationError('Срок кредита должен быть положительным')
        if term < 3:
            raise forms.ValidationError('Минимальный срок кредита - 3 месяца')
        if term > 360:
            raise forms.ValidationError('Максимальный срок кредита - 360 месяцев (30 лет)')
        return term


class ScoringDataForm(forms.ModelForm):
    """
    Форма для ввода всех признаков кредитного скоринга.
    Используется при создании кредитной заявки.
    """
    
    class Meta:
        model = ClientData
        fields = [
            # 1. Платежеспособность
            'loan_amnt', 'installment', 'annual_inc', 'dti',
            # 2. Кредитная дисциплина
            'delinq_2yrs', 'acc_now_delinq', 'pub_rec',
            'pub_rec_bankruptcies', 'collections_12_mths_ex_med',
            # 3. Кредитная нагрузка
            'revol_util', 'bc_util', 'total_bal_ex_mort',
            'total_acc', 'tot_hi_cred_lim',
            # 4. Стабильность
            'emp_length', 'home_ownership', 'earliest_cr_line',
            # 5. Поведенческий риск
            'inq_last_6mths', 'mths_since_recent_inq', 'percent_bc_gt_75',
        ]
        widgets = {
            # Платежеспособность
            'loan_amnt': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Введите сумму кредита'}),
            'installment': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Ежемесячный платеж'}),
            'annual_inc': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Годовой доход'}),
            'dti': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'DTI в процентах'}),
            
            # Кредитная дисциплина
            'delinq_2yrs': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Количество просрочек за 2 года'}),
            'acc_now_delinq': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Текущих просрочек'}),
            'pub_rec': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Публичных записей'}),
            'pub_rec_bankruptcies': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Банкротств'}),
            'collections_12_mths_ex_med': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Взысканий за 12 мес'}),
            
            # Кредитная нагрузка
            'revol_util': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Revolving utilization (%)'}),
            'bc_util': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Utilization по картам (%)'}),
            'total_bal_ex_mort': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Общий баланс без ипотеки'}),
            'total_acc': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Всего кредитов'}),
            'tot_hi_cred_lim': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Общий кредитный лимит'}),
            
            # Стабильность
            'emp_length': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Стаж работы (лет)'}),
            'home_ownership': forms.Select(attrs={'class': 'form-control'}),
            'earliest_cr_line': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            
            # Поведенческий риск
            'inq_last_6mths': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Запросов в БКИ за 6 мес'}),
            'mths_since_recent_inq': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Месяцев с последнего запроса'}),
            'percent_bc_gt_75': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '% карт с utilization > 75%'}),
        }
        labels = {
            # 1. Платежеспособность
            'loan_amnt': 'Сумма кредита (₽)',
            'installment': 'Ежемесячный платеж (₽)',
            'annual_inc': 'Годовой доход (₽)',
            'dti': 'Debt-to-Income (DTI, %)',
            
            # 2. Кредитная дисциплина
            'delinq_2yrs': 'Просрочек за 2 года',
            'acc_now_delinq': 'Текущих просрочек',
            'pub_rec': 'Публичных записей',
            'pub_rec_bankruptcies': 'Банкротств',
            'collections_12_mths_ex_med': 'Взысканий за 12 мес',
            
            # 3. Кредитная нагрузка
            'revol_util': 'Revolving utilization (%)',
            'bc_util': 'Utilization по картам (%)',
            'total_bal_ex_mort': 'Общий баланс без ипотеки (₽)',
            'total_acc': 'Всего кредитов',
            'tot_hi_cred_lim': 'Общий кредитный лимит (₽)',
            
            # 4. Стабильность
            'emp_length': 'Стаж работы (лет)',
            'home_ownership': 'Тип жилья',
            'earliest_cr_line': 'Дата первого кредита',
            
            # 5. Поведенческий риск
            'inq_last_6mths': 'Запросов в БКИ за 6 мес',
            'mths_since_recent_inq': 'Месяцев с последнего запроса',
            'percent_bc_gt_75': '% карт с utilization > 75%',
        }
    
    # ==================== Валидация полей ====================
    
    def clean_loan_amnt(self):
        amount = self.cleaned_data.get('loan_amnt')
        if amount is None:
            raise forms.ValidationError('Укажите сумму кредита')
        if amount <= 0:
            raise forms.ValidationError('Сумма кредита должна быть положительной')
        if amount < 1000:
            raise forms.ValidationError('Минимальная сумма кредита - 1 000 ₽')
        if amount > 10000000:
            raise forms.ValidationError('Максимальная сумма кредита - 10 000 000 ₽')
        return amount
    
    def clean_annual_inc(self):
        income = self.cleaned_data.get('annual_inc')
        if income is None:
            raise forms.ValidationError('Укажите годовой доход')
        if income <= 0:
            raise forms.ValidationError('Годовой доход должен быть положительным')
        if income < 10000:
            raise forms.ValidationError('Минимальный годовой доход - 10 000 ₽')
        return income
    
    def clean_dti(self):
        dti = self.cleaned_data.get('dti')
        if dti is None:
            return 0
        if dti < 0:
            raise forms.ValidationError('DTI не может быть отрицательным')
        if dti > 100:
            raise forms.ValidationError('DTI не может превышать 100%')
        return dti
    
    def clean_delinq_2yrs(self):
        val = self.cleaned_data.get('delinq_2yrs')
        if val is None:
            return 0
        if val < 0:
            raise forms.ValidationError('Количество просрочек не может быть отрицательным')
        if val > 50:
            raise forms.ValidationError('Некорректное количество просрочек')
        return val
    
    def clean_emp_length(self):
        val = self.cleaned_data.get('emp_length')
        if val is None:
            return 0
        if val < 0:
            raise forms.ValidationError('Стаж работы не может быть отрицательным')
        if val > 70:
            raise forms.ValidationError('Стаж работы не может превышать 70 лет')
        return val
    
    def clean_earliest_cr_line(self):
        val = self.cleaned_data.get('earliest_cr_line')
        if val and val > timezone.now().date():
            raise forms.ValidationError('Дата не может быть в будущем')
        return val
    
    def clean_revol_util(self):
        val = self.cleaned_data.get('revol_util')
        if val is None:
            return 0
        if val < 0:
            raise forms.ValidationError('Revolving utilization не может быть отрицательным')
        if val > 100:
            raise forms.ValidationError('Revolving utilization не может превышать 100%')
        return val
    
    def clean_bc_util(self):
        val = self.cleaned_data.get('bc_util')
        if val is None:
            return 0
        if val < 0:
            raise forms.ValidationError('Utilization по картам не может быть отрицательным')
        if val > 100:
            raise forms.ValidationError('Utilization по картам не может превышать 100%')
        return val
    
    def clean_percent_bc_gt_75(self):
        val = self.cleaned_data.get('percent_bc_gt_75')
        if val is None:
            return 0
        if val < 0:
            raise forms.ValidationError('Значение не может быть отрицательным')
        if val > 100:
            raise forms.ValidationError('Значение не может превышать 100%')
        return val
    
    def clean_total_acc(self):
        val = self.cleaned_data.get('total_acc')
        if val is None:
            return 0
        if val < 0:
            raise forms.ValidationError('Количество кредитов не может быть отрицательным')
        return val
    
    def clean(self):
        cleaned_data = super().clean()
        annual_inc = cleaned_data.get('annual_inc')
        installment = cleaned_data.get('installment')
        
        # Проверка, что ежемесячный платеж не превышает доход
        if annual_inc and installment:
            annual_inc_float = float(annual_inc)
            installment_float = float(installment)
            monthly_income = annual_inc_float / 12
            
            if installment_float > monthly_income * 0.6:
                raise forms.ValidationError(
                    'Ежемесячный платеж по кредиту не может превышать 60% ежемесячного дохода'
                )
        
        return cleaned_data


# Сохраняем старую форму для обратной совместимости (если нужно)
ClientDataForm = ScoringDataForm

class ApplicationFilterForm(forms.Form):
    """Форма фильтрации заявок"""
    
    STATUS_CHOICES = [
        ('', 'Все статусы'),
        ('Новая', 'Новая'),
        ('Одобрена', 'Одобрена'),
        ('Отказано', 'Отказано'),
        ('Требуется ручная проверка', 'Требуется ручная проверка'),
    ]
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        }),
        label='Дата с'
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        }),
        label='Дата по'
    )
    
    doc_series = forms.CharField(
        max_length=4,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Серия паспорта'
        })
    )
    
    doc_number = forms.CharField(
        max_length=6,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Номер паспорта'
        })
    )


class ManualDecisionForm(forms.Form):
    """Форма для ручного принятия решения по заявке"""
    
    DECISION_CHOICES = [
        ('approved', 'Одобрить'),
        ('rejected', 'Отклонить'),
    ]
    
    decision = forms.ChoiceField(
        choices=DECISION_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label='Решение'
    )
    
    comment = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Введите комментарий (необязательно)'
        }),
        label='Комментарий'
    )