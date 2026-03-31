# apps/clients/forms.py
from django import forms
from .models import Client

class ClientForm(forms.ModelForm):
    """Форма для добавления/редактирования клиента"""
    
    class Meta:
        model = Client
        fields = [
            'doc_series', 'doc_number',
            'last_name', 'first_name', 'middle_name',
            'birth_date', 'email', 'phone_num'
        ]
        widgets = {
            'birth_date': forms.DateInput(
                attrs={'type': 'date', 'class': 'form-control'},
                format='%Y-%m-%d'
            ),
            'doc_series': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '1234'}),
            'doc_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '123456'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Иванов'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Иван'}),
            'middle_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Иванович'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'ivan@example.com'}),
            'phone_num': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+7 (999) 123-45-67'}),
        }
        labels = {
            'doc_series': 'Серия паспорта',
            'doc_number': 'Номер паспорта',
            'last_name': 'Фамилия',
            'first_name': 'Имя',
            'middle_name': 'Отчество',
            'birth_date': 'Дата рождения',
            'email': 'Email',
            'phone_num': 'Телефон',
        }

    def clean_phone_num(self):
        """Очистка номера телефона"""
        phone = self.cleaned_data['phone_num']
        # Убираем все нецифровые символы для проверки
        cleaned = ''.join(filter(str.isdigit, phone))
        if len(cleaned) < 10 or len(cleaned) > 15:
            raise forms.ValidationError('Некорректная длина номера телефона')
        return phone

class ClientSearchForm(forms.Form):
    """Форма поиска клиента по паспорту"""
    doc_series = forms.CharField(
        max_length=4,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Серия',
            'style': 'width: 100px;'
        })
    )
    doc_number = forms.CharField(
        max_length=6,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Номер',
            'style': 'width: 150px;'
        })
    )
    
    def clean(self):
        cleaned_data = super().clean()
        series = cleaned_data.get('doc_series')
        number = cleaned_data.get('doc_number')
        
        # Если одно поле заполнено, а другое нет — ошибка
        if (series and not number) or (number and not series):
            raise forms.ValidationError('Заполните оба поля паспорта для поиска')
        
        return cleaned_data