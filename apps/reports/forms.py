# apps/reports/forms.py
from django import forms
from django.utils import timezone
from datetime import datetime

class ReportForm(forms.Form):
    """Форма для формирования отчета"""
    
    date_from = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        }),
        label='Дата с'
    )
    
    date_to = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        }),
        label='Дата по'
    )
    
    def clean(self):
        cleaned_data = super().clean()
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')
        
        if date_from and date_to and date_from > date_to:
            raise forms.ValidationError('Дата "с" не может быть позже даты "по"')
        
        if date_to and date_to > timezone.now().date():
            raise forms.ValidationError('Дата "по" не может быть позже текущей даты')
        
        return cleaned_data