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
from datetime import timedelta
from .forms import ApplicationFilterForm
from .forms import ManualDecisionForm


@login_required
def client_applications(request, client_id):
    """Отображение списка заявок выбранного клиента."""
    client = get_object_or_404(Client, pk=client_id)
    applications = CreditApplication.objects.filter(client=client).select_related(
        'status', 'system_decision', 'risk_category'
    ).order_by('-created_at')

    # Пагинация списка заявок клиента.
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
    """Создание кредитной заявки и связанных скоринговых данных клиента."""
    client = get_object_or_404(Client, pk=client_id)
    
    if request.method == 'POST':
        # Инициализация двух форм: признаки скоринга и параметры кредитного продукта.
        scoring_form = ScoringDataForm(request.POST)
        application_form = CreditApplicationForm(request.POST)
        
        if scoring_form.is_valid() and application_form.is_valid():
            # Сохранение финансовых признаков, использующихся моделью.
            client_data = scoring_form.save(commit=False)
            client_data.client = client
            client_data.save()
            
            # Назначение стартового статуса заявки.
            new_status, _ = ApplicationStatus.objects.get_or_create(
                type='Новая',
                defaults={'description': 'Только создана, скоринг не проводился'}
            )
            
            # Создание кредитной заявки с привязкой к клиенту и сохраненным признакам.
            application = application_form.save(commit=False)
            application.client = client
            application.client_data = client_data
            application.created_by = request.user
            application.status = new_status
            application.save()
            
            messages.success(request, f'Заявка №{application.app_num} успешно создана')
            return redirect('credit:client_applications', client_id=client.id)
        else:
            # Вывод диагностических сообщений при невалидных данных формы.
            if scoring_form.errors:
                messages.error(request, 'Пожалуйста, исправьте ошибки в финансовых данных')
            if application_form.errors:
                messages.error(request, 'Пожалуйста, исправьте ошибки в параметрах кредита')
    else:
        # Предзаполнение формы последними доступными финансовыми данными клиента.
        last_client_data = ClientData.objects.filter(client=client).first()
        
        if last_client_data:
            scoring_form = ScoringDataForm(instance=last_client_data)
        else:
            scoring_form = ScoringDataForm()
        
        # Инициализация формы параметров кредита.
        initial_application = {}
        application_form = CreditApplicationForm(initial=initial_application)
    
    return render(request, 'credit/application_form.html', {
        'client': client,
        'scoring_form': scoring_form,
        'application_form': application_form,
    })


@login_required
def application_detail(request, pk):
    """Детальный просмотр заявки и связанных сущностей скорингового процесса."""
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
    """Выполнение ML-скоринга по выбранной заявке."""
    application = get_object_or_404(
        CreditApplication.objects.select_related('client_data', 'status'),
        pk=pk
    )
    
    # Контроль повторного скоринга: заявка обрабатывается моделью однократно.
    if application.scoring_date is not None:
        messages.warning(request, 'Данная заявка уже была оценена')
        return redirect('credit:application_detail', pk=application.pk)
    
    try:
        # Запуск модели и получение числового прогноза.
        result = predict_application(application)
        
        # Формирование объясняющих факторов для итогового решения.
        factors = get_shap_factors(application)
        
        # Сохранение ключевых метрик скоринга в объект заявки.
        application.scoring_score = result['score']
        application.probability_default = result['probability']
        application.scoring_date = timezone.now()
        application.top_factors = factors
        
        # Назначение системного решения, категории риска и статуса заявки.
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
    """Отображение общего реестра заявок с фильтрацией и статистикой."""
    # Инициализация формы фильтрации входными query-параметрами.
    filter_form = ApplicationFilterForm(request.GET or None)
    
    # Базовая выборка заявок с необходимыми связанными сущностями.
    applications = CreditApplication.objects.all().select_related(
        'client', 'status', 'system_decision', 'risk_category'
    ).order_by('-created_at')
    
    if filter_form.is_valid():
        # Фильтрация по статусу обработки заявки.
        status = filter_form.cleaned_data.get('status')
        if status:
            applications = applications.filter(status__type__iexact=status)
        
        # Фильтрация по нижней границе даты создания.
        date_from = filter_form.cleaned_data.get('date_from')
        if date_from:
            applications = applications.filter(created_at__date__gte=date_from)
        
        date_to = filter_form.cleaned_data.get('date_to')
        if date_to:
            applications = applications.filter(created_at__date__lte=date_to)
        
        # Фильтрация по паспорту клиента.
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
    else:
        # Ограничение периода по умолчанию при отсутствии валидного фильтра.
        one_month_ago = timezone.now() - timedelta(days=30)
        applications = applications.filter(created_at__gte=one_month_ago)
    
    # Пагинация итоговой выборки.
    paginator = Paginator(applications, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Расчет агрегированной статистики для дашборда списка заявок.
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

@login_required
def select_client_for_application(request):
    """Поиск клиента для запуска процесса создания заявки."""
    # Фильтрация по паспорту.
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
    
    # Пагинация результатов поиска.
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
    """Ручное изменение статуса заявки и фиксация истории решения."""
    application = get_object_or_404(
        CreditApplication.objects.select_related('status', 'client'),
        pk=pk
    )
    
    if request.method == 'POST':
        form = ManualDecisionForm(request.POST)
        if form.is_valid():
            decision = form.cleaned_data['decision']
            comment = form.cleaned_data.get('comment', '')
            
            # Сохранение состояния заявки до ручной корректировки.
            old_status = application.status.type
            old_decision = application.system_decision.decision if application.system_decision else None
            
            if decision == 'approved':
                # Ручное одобрение заявки.
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
                # Ручной отказ по заявке.
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
            
            # Применение нового статуса и служебных атрибутов к заявке.
            application.status = new_status
            application.system_decision = system_decision
            application.risk_category = risk_category
            
            # Формирование блока истории ручного решения.
            manual_history = {
                'old_status': old_status,
                'old_decision': old_decision,
                'new_status': new_status.type,
                'new_decision': system_decision.decision,
                'manual_decision_by': request.user.get_full_name(),
                'manual_decision_date': timezone.now().isoformat(),
                'comment': comment,
                'previous_scoring_score': application.scoring_score,
                'previous_probability': application.probability_default,
            }
            
            # Нормализация структуры `top_factors` перед добавлением истории.
            if application.top_factors is None:
                application.top_factors = {'manual_history': [manual_history]}
            elif isinstance(application.top_factors, dict):
                if 'manual_history' not in application.top_factors:
                    application.top_factors['manual_history'] = []
                application.top_factors['manual_history'].append(manual_history)
            elif isinstance(application.top_factors, list):
                application.top_factors = {'manual_history': [manual_history]}
            else:
                application.top_factors = {'manual_history': [manual_history]}
            
            application.save()
            
            return redirect('credit:application_detail', pk=application.pk)
    else:
        form = ManualDecisionForm()
    
    return render(request, 'credit/manual_decision.html', {
        'application': application,
        'form': form,
    })