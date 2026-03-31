# apps/clients/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Client
from .forms import ClientForm, ClientSearchForm

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
def client_detail(request, pk):
    """Детальная информация о клиенте"""
    client = get_object_or_404(Client, pk=pk)
    return render(request, 'clients/client_detail.html', {
        'client': client
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