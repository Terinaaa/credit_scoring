from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from apps.credit.models import CreditApplication
from apps.scoring.models import ApplicationStatus

@login_required
def dashboard_view(request):
    # Получаем текущую дату и время
    now = timezone.now()
    current_date = now.strftime('%d.%m.%Y')
    current_time = now.strftime('%H:%M:%S')
    
    # Получаем статусы
    try:
        new_status = ApplicationStatus.objects.get(type='Новая')
        manual_status = ApplicationStatus.objects.get(type='Требуется ручная проверка')
        
        # Количество заявок со статусом "Новая"
        new_applications_count = CreditApplication.objects.filter(
            status=new_status
        ).count()
        
        # Количество заявок со статусом "Требуется ручная проверка"
        manual_applications_count = CreditApplication.objects.filter(
            status=manual_status
        ).count()
        
    except ApplicationStatus.DoesNotExist:
        new_applications_count = 0
        manual_applications_count = 0
    
    context = {
        'user_name': request.user.first_name or request.user.username,
        'current_date': current_date,
        'current_time': current_time,
        'new_applications_count': new_applications_count,
        'manual_applications_count': manual_applications_count,
    }
    
    return render(request, 'dashboard/dashboard.html', context)