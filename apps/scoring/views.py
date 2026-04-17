# scoring/views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import ScoringInputForm
from .ml_service import predict

@login_required
def scoring_view(request):
    """Форма разового скоринга с расчетом вероятности дефолта."""
    result = None
    
    if request.method == 'POST':
        form = ScoringInputForm(request.POST)
        if form.is_valid():
            try:
                # Запуск ML-сервиса для оценки введенных признаков заемщика.
                result = predict(form.cleaned_data)
                messages.success(request, 'Скоринг успешно выполнен!')
            except Exception as e:
                messages.error(request, f'Ошибка при расчете: {e}')
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме')
    else:
        form = ScoringInputForm()
    
    return render(request, 'scoring/scoring_form.html', {
        'form': form,
        'result': result
    })