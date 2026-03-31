# scoring/forms.py
from django import forms

class ScoringInputForm(forms.Form):
    # Платежеспособность
    loan_amnt = forms.FloatField(label='Сумма кредита', min_value=1000)
    installment = forms.FloatField(label='Ежемесячный платеж')
    annual_inc = forms.FloatField(label='Годовой доход')
    dti = forms.FloatField(label='Debt-to-Income (DTI)', help_text='В процентах')
    
    # Кредитная дисциплина
    delinq_2yrs = forms.IntegerField(label='Просрочек за 2 года', initial=0)
    acc_now_delinq = forms.IntegerField(label='Текущих просрочек', initial=0)
    pub_rec = forms.IntegerField(label='Публичных записей', initial=0)
    pub_rec_bankruptcies = forms.IntegerField(label='Банкротств', initial=0)
    collections_12_mths_ex_med = forms.IntegerField(label='Взысканий за 12 мес', initial=0)
    
    # Кредитная нагрузка
    revol_util = forms.FloatField(label='Revolving utilization', help_text='В процентах')
    bc_util = forms.FloatField(label='Utilization по картам', help_text='В процентах')
    total_bal_ex_mort = forms.FloatField(label='Общий баланс без ипотеки')
    total_acc = forms.IntegerField(label='Всего кредитов')
    tot_hi_cred_lim = forms.FloatField(label='Общий кредитный лимит')
    
    # Стабильность
    emp_length = forms.ChoiceField(label='Стаж работы', choices=[
        ('<1 year', 'Менее года'),
        ('1 year', '1 год'),
        ('2 years', '2 года'),
        ('3 years', '3 года'),
        ('4 years', '4 года'),
        ('5 years', '5 лет'),
        ('6 years', '6 лет'),
        ('7 years', '7 лет'),
        ('8 years', '8 лет'),
        ('9 years', '9 лет'),
        ('10+ years', '10+ лет')
    ])
    home_ownership = forms.ChoiceField(label='Тип жилья', choices=[
        ('RENT', 'Аренда'),
        ('MORTGAGE', 'Ипотека'),
        ('OWN', 'Собственное'),
        ('OTHER', 'Другое')
    ])
    earliest_cr_line = forms.CharField(label='Дата первого кредита', help_text='Например: Jan-2005')
    
    # Поведенческий риск
    inq_last_6mths = forms.IntegerField(label='Запросов в БКИ за 6 мес', initial=0)
    mths_since_recent_inq = forms.FloatField(label='Месяцев с последнего запроса')
    percent_bc_gt_75 = forms.FloatField(label='% карт с utilization > 75%')