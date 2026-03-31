# apps/scoring/admin.py
from django.contrib import admin
from .models import EmploymentType, ApplicationStatus, SystemDecision, RiskCategory, ScoringResult

@admin.register(EmploymentType)
class EmploymentTypeAdmin(admin.ModelAdmin):
    list_display = ('type', 'description')
    search_fields = ('type',)
    ordering = ('type',)

@admin.register(ApplicationStatus)
class ApplicationStatusAdmin(admin.ModelAdmin):
    list_display = ('type', 'description')
    search_fields = ('type',)
    ordering = ('type',)

@admin.register(SystemDecision)
class SystemDecisionAdmin(admin.ModelAdmin):
    list_display = ('decision', 'description')
    search_fields = ('decision',)
    ordering = ('decision',)

@admin.register(RiskCategory)
class RiskCategoryAdmin(admin.ModelAdmin):
    list_display = ('category', 'description')
    ordering = ('category',)
    # category уже primary key, редактируем осторожно

@admin.register(ScoringResult)
class ScoringResultAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'client', 'created_at', 'probability', 'score', 'recommendation')
    list_filter = ('created_at', 'recommendation')
    search_fields = ('user__username', 'client__last_name')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'
    
    def has_add_permission(self, request):
        return False  # Результаты скоринга создаются только через ML-модель