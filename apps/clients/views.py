# apps/clients/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Client, ClientData
from .forms import ClientForm, ClientSearchForm
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from apps.credit.models import CreditApplication
from django.db import models

@login_required
def client_list(request):
    """Список клиентов с поиском по паспорту"""
    clients = Client.objects.all()
    search_form = ClientSearchForm(request.GET or None)
    
    if search_form.is_valid():
        series = search_form.cleaned_data.get('doc_series')
        number = search_form.cleaned_data.get('doc_number')
        
        if series and number:
            clients = clients.filter(
                doc_series=series,
                doc_number=number
            )
            if not clients.exists():
                messages.info(request, f'Клиенты с паспортом {series} {number} не найдены')
    
    # Пагинация
    paginator = Paginator(clients, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'clients/client_list.html', {
        'page_obj': page_obj,
        'search_form': search_form,
        'clients_count': clients.count()
    })

@login_required
def client_add(request):
    """Добавление нового клиента"""
    if request.method == 'POST':
        form = ClientForm(request.POST)
        if form.is_valid():
            client = form.save(commit=False)
            client.created_by = request.user
            client.save()
            messages.success(request, f'Клиент {client.get_full_name()} успешно добавлен')
            return redirect('clients:client_list')
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме')
    else:
        form = ClientForm()
    
    return render(request, 'clients/client_form.html', {
        'form': form,
        'title': 'Добавление клиента'
    })

@login_required
def client_edit(request, pk):
    """Редактирование клиента"""
    client = get_object_or_404(Client, pk=pk)
    
    if request.method == 'POST':
        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            form.save()
            messages.success(request, f'Данные клиента обновлены')
            return redirect('clients:client_list')
    else:
        form = ClientForm(instance=client)
    
    return render(request, 'clients/client_form.html', {
        'form': form,
        'client': client,
        'title': f'Редактирование: {client.get_full_name()}'
    })

@login_required
def client_data_view(request, pk):
    """
    Просмотр всех финансовых данных клиента
    """
    client = get_object_or_404(Client, pk=pk)
    
    # Получаем все финансовые данные клиента (последние сверху)
    financial_data = ClientData.objects.filter(client=client).order_by('-created_at')
    
    # Получаем все кредитные заявки клиента (для статистики)
    applications = CreditApplication.objects.filter(client=client).select_related(
        'status', 'system_decision', 'risk_category'
    ).order_by('-created_at')
    
    # Пагинация для финансовых данных
    paginator = Paginator(financial_data, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Расчет среднего ежемесячного дохода (из годового дохода)
    avg_monthly_income = 0
    if financial_data.exists():
        # Считаем средний годовой доход
        avg_annual = financial_data.aggregate(models.Avg('annual_inc'))['annual_inc__avg']
        if avg_annual:
            # Переводим в ежемесячный
            avg_monthly_income = avg_annual / 12
    
    # Статистика по клиенту
    stats = {
        'total_financial_records': financial_data.count(),
        'total_applications': applications.count(),
        'last_application_date': applications.first().created_at if applications.exists() else None,
        'avg_monthly_income': avg_monthly_income,
    }
    
    return render(request, 'clients/client_data.html', {
        'client': client,
        'financial_data': page_obj,
        'applications': applications,
        'stats': stats,
    })

@login_required
def client_delete(request, pk):
    """Удаление клиента"""
    client = get_object_or_404(Client, pk=pk)
    
    if request.method == 'POST':
        client.delete()
        messages.success(request, f'Клиент удален')
        return redirect('clients:client_list')
    
    return render(request, 'clients/client_confirm_delete.html', {
        'client': client
    })

@require_GET
@login_required
def get_client_by_passport(request):
    """
    AJAX-эндпоинт для получения данных клиента по паспорту
    """
    doc_series = request.GET.get('doc_series', '').strip()
    doc_number = request.GET.get('doc_number', '').strip()
    
    if not doc_series or not doc_number:
        return JsonResponse({'error': 'Не указаны паспортные данные'}, status=400)
    
    try:
        client = Client.objects.get(doc_series=doc_series, doc_number=doc_number)
        
        data = {
            'exists': True,
            'id': client.id,
            'first_name': client.first_name,
            'last_name': client.last_name,
            'middle_name': client.middle_name or '',
            'birth_date': client.birth_date.strftime('%Y-%m-%d'),
            'email': client.email,
            'phone_num': client.phone_num,
        }
        return JsonResponse(data)
        
    except Client.DoesNotExist:
        return JsonResponse({'exists': False, 'error': 'Клиент не найден'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)