# apps/credit/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from apps.clients.models import Client, ClientData
from apps.scoring.models import ApplicationStatus
from .models import CreditApplication
from .forms import ScoringDataForm, CreditApplicationForm
from django.utils import timezone
from .ml_scoring import predict_application, get_shap_factors
from apps.scoring.models import SystemDecision, RiskCategory
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta
from .forms import ApplicationFilterForm
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .forms import ManualDecisionForm
from apps.scoring.models import SystemDecision, RiskCategory


@login_required
def client_applications(request, client_id):
    """Список заявок клиента"""
    client = get_object_or_404(Client, pk=client_id)
    applications = CreditApplication.objects.filter(client=client).select_related(
        'status', 'system_decision', 'risk_category'
    ).order_by('-created_at')

    # Пагинация
    paginator = Paginator(applications, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'credit/client_applications.html', {
        'client': client,
        'page_obj': page_obj,
        'applications': applications,
    })


@login_required
def application_create(request, client_id):
    """
    Создание новой кредитной заявки.
    Использует ScoringDataForm для ввода всех признаков модели.
    """
    client = get_object_or_404(Client, pk=client_id)
    
    if request.method == 'POST':
        # Используем ScoringDataForm для всех признаков скоринга
        scoring_form = ScoringDataForm(request.POST)
        application_form = CreditApplicationForm(request.POST)
        
        if scoring_form.is_valid() and application_form.is_valid():
            # 1. Сохраняем финансовые данные клиента (все признаки)
            client_data = scoring_form.save(commit=False)
            client_data.client = client
            client_data.save()
            
            # 2. Получаем статус "Новая"
            new_status, _ = ApplicationStatus.objects.get_or_create(
                type='Новая',
                defaults={'description': 'Только создана, скоринг не проводился'}
            )
            
            # 3. Создаем заявку
            application = application_form.save(commit=False)
            application.client = client
            application.client_data = client_data
            application.created_by = request.user
            application.status = new_status
            application.save()
            
            messages.success(request, f'Заявка №{application.app_num} успешно создана')
            return redirect('credit:client_applications', client_id=client.id)
        else:
            # Форма невалидна - показываем ошибки
            if scoring_form.errors:
                messages.error(request, 'Пожалуйста, исправьте ошибки в финансовых данных')
            if application_form.errors:
                messages.error(request, 'Пожалуйста, исправьте ошибки в параметрах кредита')
    else:
        # GET запрос - предзаполняем форму последними данными клиента
        last_client_data = ClientData.objects.filter(client=client).first()
        
        if last_client_data:
            # Используем последние данные для предзаполнения
            scoring_form = ScoringDataForm(instance=last_client_data)
        else:
            scoring_form = ScoringDataForm()
        
        # Для параметров кредита можно предзаполнить значения по умолчанию
        initial_application = {}
        application_form = CreditApplicationForm(initial=initial_application)
    
    return render(request, 'credit/application_form.html', {
        'client': client,
        'scoring_form': scoring_form,      # переименовано для ясности
        'application_form': application_form,
    })


@login_required
def application_detail(request, pk):
    """
    Детальный просмотр заявки с отображением всех признаков скоринга.
    """
    application = get_object_or_404(
        CreditApplication.objects.select_related(
            'client', 'client_data', 'status', 'system_decision', 'risk_category'
        ),
        pk=pk
    )
    
    return render(request, 'credit/application_detail.html', {
        'application': application
    })

@login_required
def application_score(request, pk):
    """
    Оценка кредитоспособности по заявке с помощью ML-модели
    """
    application = get_object_or_404(
        CreditApplication.objects.select_related('client_data', 'status'),
        pk=pk
    )
    
    # Проверяем, не оценивалась ли уже заявка
    if application.scoring_date is not None:
        messages.warning(request, 'Данная заявка уже была оценена')
        return redirect('credit:application_detail', pk=application.pk)
    
    try:
        # Получаем предсказание
        result = predict_application(application)
        
        # Получаем SHAP факторы
        factors = get_shap_factors(application)
        
        # Обновляем заявку результатами скоринга
        application.scoring_score = result['score']
        application.probability_default = result['probability']
        application.scoring_date = timezone.now()
        application.top_factors = factors  # Используем существующее поле top_factors
        
        # Определяем системное решение и категорию риска
        if result['decision'] == 'AUTO_APPROVE':
            system_decision, _ = SystemDecision.objects.get_or_create(
                decision='AUTO_APPROVE',
                defaults={'description': 'Автоматическое одобрение'}
            )
            risk_category, _ = RiskCategory.objects.get_or_create(
                category=1,
                defaults={'description': 'Низкий риск'}
            )
            status, _ = ApplicationStatus.objects.get_or_create(
                type='Одобрена',
                defaults={'description': 'Кредит одобрен'}
            )
        elif result['decision'] == 'AUTO_REJECT':
            system_decision, _ = SystemDecision.objects.get_or_create(
                decision='AUTO_REJECT',
                defaults={'description': 'Автоматический отказ'}
            )
            risk_category, _ = RiskCategory.objects.get_or_create(
                category=5,
                defaults={'description': 'Очень высокий риск'}
            )
            status, _ = ApplicationStatus.objects.get_or_create(
                type='Отказано',
                defaults={'description': 'В выдаче кредита отказано'}
            )
        else:
            system_decision, _ = SystemDecision.objects.get_or_create(
                decision='MANUAL_REVIEW',
                defaults={'description': 'Требуется ручная проверка'}
            )
            risk_category, _ = RiskCategory.objects.get_or_create(
                category=3,
                defaults={'description': 'Средний риск'}
            )
            status, _ = ApplicationStatus.objects.get_or_create(
                type='Требуется ручная проверка',
                defaults={'description': 'Решение не автоматическое'}
            )
        
        application.system_decision = system_decision
        application.risk_category = risk_category
        application.status = status
        
        application.save()
        
        messages.success(
            request, 
            f'Скоринг выполнен! Балл: {result["score"]}, Решение: {result["decision_ru"]}'
        )
        
    except Exception as e:
        messages.error(request, f'Ошибка при выполнении скоринга: {e}')
    
    return redirect('credit:application_detail', pk=application.pk)

@login_required
def application_list(request):
    """
    Список всех заявок с фильтрацией
    Доступен для кредитных менеджеров и руководителей
    """
    # Базовый запрос: заявки за последний месяц
    one_month_ago = timezone.now() - timedelta(days=30)
    applications = CreditApplication.objects.filter(
        created_at__gte=one_month_ago
    ).select_related(
        'client', 'status', 'system_decision', 'risk_category'
    ).order_by('-created_at')
    
    # Форма фильтрации
    filter_form = ApplicationFilterForm(request.GET or None)
    
    if filter_form.is_valid():
        # Фильтр по статусу
        status = filter_form.cleaned_data.get('status')
        if status:
            applications = applications.filter(status__type=status)
        
        # Фильтр по дате
        date_from = filter_form.cleaned_data.get('date_from')
        if date_from:
            applications = applications.filter(created_at__date__gte=date_from)
        
        date_to = filter_form.cleaned_data.get('date_to')
        if date_to:
            applications = applications.filter(created_at__date__lte=date_to)
        
        # Фильтр по паспортным данным
        doc_series = filter_form.cleaned_data.get('doc_series')
        doc_number = filter_form.cleaned_data.get('doc_number')
        
        if doc_series and doc_number:
            applications = applications.filter(
                client__doc_series=doc_series,
                client__doc_number=doc_number
            )
        elif doc_series:
            applications = applications.filter(client__doc_series=doc_series)
        elif doc_number:
            applications = applications.filter(client__doc_number=doc_number)
    
    # Пагинация
    paginator = Paginator(applications, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Статистика по заявкам
    stats = {
        'total': applications.count(),
        'approved': applications.filter(status__type='Одобрена').count(),
        'rejected': applications.filter(status__type='Отказано').count(),
        'pending': applications.filter(status__type='Новая').count(),
        'manual': applications.filter(status__type='Требуется ручная проверка').count(),
    }
    
    return render(request, 'credit/application_list.html', {
        'page_obj': page_obj,
        'filter_form': filter_form,
        'stats': stats,
    })

@require_GET
@login_required
def get_client_by_passport(request):
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
    
@login_required
def select_client_for_application(request):
    # Поиск по паспорту
    doc_series = request.GET.get('doc_series', '').strip()
    doc_number = request.GET.get('doc_number', '').strip()
    clients = Client.objects.all()
    search_performed = False
    
    if doc_series or doc_number:
        search_performed = True
        if doc_series and doc_number:
            clients = clients.filter(doc_series=doc_series, doc_number=doc_number)
        elif doc_series:
            clients = clients.filter(doc_series=doc_series)
        elif doc_number:
            clients = clients.filter(doc_number=doc_number)
    
    # Пагинация
    paginator = Paginator(clients, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'credit/select_client.html', {
        'page_obj': page_obj,
        'clients_count': clients.count(),
        'search_performed': search_performed,
        'doc_series': doc_series,
        'doc_number': doc_number,
    })

@login_required
def manual_decision(request, pk):
    """
    Ручное изменение статуса заявки (для заявок с ручной проверкой)
    """
    application = get_object_or_404(
        CreditApplication.objects.select_related('status', 'client'),
        pk=pk
    )
    
    # Проверяем, что заявка действительно требует ручной проверки
    if application.status.type != 'Требуется ручная проверка':
        messages.error(request, 'Только заявки со статусом "Требуется ручная проверка" могут быть изменены вручную')
        return redirect('credit:application_detail', pk=application.pk)
    
    if request.method == 'POST':
        form = ManualDecisionForm(request.POST)
        if form.is_valid():
            decision = form.cleaned_data['decision']
            comment = form.cleaned_data.get('comment', '')
            
            if decision == 'approved':
                # Одобряем заявку
                new_status, _ = ApplicationStatus.objects.get_or_create(
                    type='Одобрена',
                    defaults={'description': 'Кредит одобрен'}
                )
                system_decision, _ = SystemDecision.objects.get_or_create(
                    decision='MANUAL_APPROVE',
                    defaults={'description': 'Одобрено вручную'}
                )
                risk_category, _ = RiskCategory.objects.get_or_create(
                    category=2,
                    defaults={'description': 'Умеренный риск (ручное одобрение)'}
                )
                messages.success(request, f'Заявка №{application.app_num} одобрена вручную')
                
            elif decision == 'rejected':
                # Отклоняем заявку
                new_status, _ = ApplicationStatus.objects.get_or_create(
                    type='Отказано',
                    defaults={'description': 'В выдаче кредита отказано'}
                )
                system_decision, _ = SystemDecision.objects.get_or_create(
                    decision='MANUAL_REJECT',
                    defaults={'description': 'Отказано вручную'}
                )
                risk_category, _ = RiskCategory.objects.get_or_create(
                    category=4,
                    defaults={'description': 'Высокий риск (ручной отказ)'}
                )
                messages.warning(request, f'Заявка №{application.app_num} отклонена вручную')
            
            # Обновляем заявку
            application.status = new_status
            application.system_decision = system_decision
            application.risk_category = risk_category
            
            # Добавляем комментарий в JSON-поле, если есть
            if comment:
                if application.top_factors:
                    application.top_factors['manual_comment'] = comment
                    application.top_factors['manual_decision_by'] = request.user.get_full_name()
                    application.top_factors['manual_decision_date'] = timezone.now().isoformat()
                else:
                    application.top_factors = {
                        'manual_comment': comment,
                        'manual_decision_by': request.user.get_full_name(),
                        'manual_decision_date': timezone.now().isoformat()
                    }
            
            application.save()
            
            return redirect('credit:application_detail', pk=application.pk)
    else:
        form = ManualDecisionForm()
    
    return render(request, 'credit/manual_decision.html', {
        'application': application,
        'form': form,
    })