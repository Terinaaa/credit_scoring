# scoring/views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import ScoringInputForm
from .ml_service import predict
#from .models import ScoringResult  # если хотите сохранять историю

@login_required
def scoring_view(request):
    result = None
    form_data = None
    
    if request.method == 'POST':
        form = ScoringInputForm(request.POST)
        if form.is_valid():
            form_data = form.cleaned_data
            try:
                # Вызываем ML модель
                result = predict(form_data)
                messages.success(request, 'Скоринг успешно выполнен!')
                
                # Сохраняем в историю (опционально)
                # ScoringResult.objects.create(
                #     user=request.user,
                #     input_data=form_data,
                #     probability=result['probability_raw'],
                #     decision=result['decision'],
                #     score=result['score']
                # )
                
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