# apps/reports/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import datetime, timedelta
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
matplotlib.use('Agg')
from django.http import FileResponse
from .forms import ReportForm
from apps.credit.models import CreditApplication
from apps.scoring.models import ApplicationStatus
import os
import io
from collections import defaultdict

# Регистрируем шрифт с поддержкой кириллицы
def register_russian_font():
    """Регистрация шрифта для поддержки кириллицы"""
    try:
        font_paths = [
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/ariali.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/System/Library/Fonts/Helvetica.ttc"
        ]
        
        for font_path in font_paths:
            if os.path.exists(font_path):
                pdfmetrics.registerFont(TTFont('RussianFont', font_path))
                print(f"Шрифт загружен: {font_path}")
                return True
        print("Шрифт для кириллицы не найден, используется стандартный")
        return False
    except Exception as e:
        print(f"Ошибка загрузки шрифта: {e}")
        return False

HAS_RUSSIAN_FONT = register_russian_font()


@login_required
def report_view(request):
    """Страница формирования отчета"""
    today = timezone.now().date()
    default_from = today - timedelta(days=30)
    
    if request.method == 'POST':
        form = ReportForm(request.POST)
        if form.is_valid():
            date_from = form.cleaned_data['date_from']
            date_to = form.cleaned_data['date_to']
            
            return generate_pdf_report(request, date_from, date_to)
    else:
        form = ReportForm(initial={
            'date_from': default_from,
            'date_to': today
        })
    
    return render(request, 'reports/report_form.html', {
        'form': form
    })


def generate_pdf_report(request, date_from, date_to):
    """Генерация PDF-отчета"""
    
    # Добавляем один день для включения конечной даты
    date_to_end = date_to + timedelta(days=1)
    
    # Получаем данные
    applications = CreditApplication.objects.filter(
        created_at__date__gte=date_from,
        created_at__date__lt=date_to_end
    ).select_related('status', 'system_decision')
    
    total_applications = applications.count()
    processed_applications = applications.exclude(status__type='Новая').count()
    
    approved_count = applications.filter(status__type='Одобрена').count()
    rejected_count = applications.filter(status__type='Отказано').count()
    manual_count = applications.filter(status__type='Требуется ручная проверка').count()
    new_count = applications.filter(status__type='Новая').count()
    
    # ========== ДАННЫЕ ПО МЕСЯЦАМ ДЛЯ СТОЛБЧАТОЙ ДИАГРАММЫ ==========
    monthly_data = defaultdict(lambda: {'total': 0, 'approved': 0, 'rejected': 0, 'manual': 0})
    
    for app in applications:
        month_key = app.created_at.strftime('%Y-%m')
        month_label = app.created_at.strftime('%b %Y')  # Например: "Jan 2024"
        
        monthly_data[month_key]['label'] = month_label
        monthly_data[month_key]['total'] += 1
        
        if app.status.type == 'Одобрена':
            monthly_data[month_key]['approved'] += 1
        elif app.status.type == 'Отказано':
            monthly_data[month_key]['rejected'] += 1
        elif app.status.type == 'Требуется ручная проверка':
            monthly_data[month_key]['manual'] += 1
    
    # Сортируем по дате
    sorted_months = sorted(monthly_data.keys())
    
    months_labels = [monthly_data[m]['label'] for m in sorted_months]
    total_counts = [monthly_data[m]['total'] for m in sorted_months]
    approved_counts = [monthly_data[m]['approved'] for m in sorted_months]
    rejected_counts = [monthly_data[m]['rejected'] for m in sorted_months]
    manual_counts = [monthly_data[m]['manual'] for m in sorted_months]
    
    # ========== СОЗДАЕМ СТОЛБЧАТУЮ ДИАГРАММУ ==========
    fig, ax = plt.subplots(figsize=(12, 6))
    
    x = np.arange(len(months_labels))
    width = 0.25  # Ширина столбцов
    
    # Столбцы для разных статусов
    bars_approved = ax.bar(x - width, approved_counts, width, label='Одобрено', color='#28a745')
    bars_rejected = ax.bar(x, rejected_counts, width, label='Отказано', color='#dc3545')
    bars_manual = ax.bar(x + width, manual_counts, width, label='Ручная проверка', color='#ffc107')
    
    # Добавляем линии для общего количества
    ax.plot(x, total_counts, 'o-', color='#007bff', linewidth=2, markersize=8, label='Всего заявок')
    
    # Настройка диаграммы
    ax.set_xlabel('Месяц', fontsize=12)
    ax.set_ylabel('Количество заявок', fontsize=12)
    ax.set_title('Динамика заявок по месяцам', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(months_labels, rotation=45, ha='right')
    ax.legend(loc='upper left')
    
    # Добавляем значения на столбцы
    for bars in [bars_approved, bars_rejected, bars_manual]:
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                ax.annotate(f'{int(height)}',
                           xy=(bar.get_x() + bar.get_width() / 2, height),
                           xytext=(0, 3),
                           textcoords="offset points",
                           ha='center', va='bottom', fontsize=8)
    
    # Добавляем значения на линию общего количества
    for i, (month, count) in enumerate(zip(months_labels, total_counts)):
        ax.annotate(f'{count}',
                   xy=(i, count),
                   xytext=(0, 10),
                   textcoords="offset points",
                   ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    plt.tight_layout()
    
    # Сохраняем диаграмму
    chart_buffer = io.BytesIO()
    plt.savefig(chart_buffer, format='png', bbox_inches='tight', dpi=150)
    chart_buffer.seek(0)
    plt.close()
    
    # ========== СОЗДАЕМ КРУГОВУЮ ДИАГРАММУ ==========
    fig2, ax2 = plt.subplots(figsize=(5, 4))
    decisions_data = [approved_count, rejected_count, manual_count]
    decisions_labels = ['Одобрено', 'Отказано', 'Ручная проверка']
    colors_list = ['#28a745', '#dc3545', '#ffc107']
    
    if sum(decisions_data) > 0:
        ax2.pie(
            decisions_data,
            labels=decisions_labels,
            colors=colors_list,
            autopct=lambda pct: f'{pct:.1f}%' if pct > 0 else '',
            startangle=90
        )
        ax2.set_title('Общее распределение решений', fontsize=12)
    else:
        ax2.text(0.5, 0.5, 'Нет данных за выбранный период', 
                ha='center', va='center', transform=ax2.transAxes)
    
    pie_buffer = io.BytesIO()
    plt.savefig(pie_buffer, format='png', bbox_inches='tight', dpi=150)
    pie_buffer.seek(0)
    plt.close()
    
    # ========== СОЗДАЕМ PDF ==========
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        title=f'Report_{date_from.strftime("%Y%m%d")}_{date_to.strftime("%Y%m%d")}'
    )
    
    styles = getSampleStyleSheet()
    font_name = 'RussianFont' if HAS_RUSSIAN_FONT else 'Helvetica'
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontName=font_name,
        fontSize=16,
        textColor=colors.HexColor('#2c3e50'),
        alignment=1,
        spaceAfter=20
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontName=font_name,
        fontSize=12,
        textColor=colors.HexColor('#34495e'),
        spaceAfter=10
    )
    
    normal_style = ParagraphStyle(
        'Normal',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=10
    )
    
    table_style = ParagraphStyle(
        'TableStyle',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=9
    )
    
    story = []
    
    # Заголовок
    story.append(Paragraph('Отчет по кредитным заявкам', title_style))
    story.append(Paragraph(f'Период: {date_from.strftime("%d.%m.%Y")} - {date_to.strftime("%d.%m.%Y")}', normal_style))
    story.append(Spacer(1, 20))
    
    # Основная статистика
    story.append(Paragraph('Общая статистика', heading_style))
    
    stats_data = [
        [Paragraph('Показатель', table_style), Paragraph('Значение', table_style)],
        [Paragraph('Всего заявок', table_style), Paragraph(str(total_applications), table_style)],
        [Paragraph('Обработано заявок', table_style), Paragraph(str(processed_applications), table_style)],
        [Paragraph('Осталось в работе', table_style), Paragraph(str(new_count), table_style)],
    ]
    
    stats_table = Table(stats_data, colWidths=[200, 100])
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, 0), font_name),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('FONTNAME', (0, 1), (-1, -1), font_name),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    story.append(stats_table)
    story.append(Spacer(1, 20))
    
    # Столбчатая диаграмма по месяцам
    story.append(Paragraph('Динамика заявок по месяцам', heading_style))
    chart_img = Image(chart_buffer, width=18*cm, height=9*cm)
    story.append(chart_img)
    story.append(Spacer(1, 20))
    
    # Круговая диаграмма
    story.append(Paragraph('Общее распределение решений', heading_style))
    pie_img = Image(pie_buffer, width=12*cm, height=10*cm)
    story.append(pie_img)
    story.append(Spacer(1, 20))
    
    # Таблица решений
    decision_data = [
        [Paragraph('Решение', table_style), Paragraph('Количество', table_style), Paragraph('Процент', table_style)],
        [Paragraph('Одобрено', table_style), Paragraph(str(approved_count), table_style), 
         Paragraph(f'{approved_count/total_applications*100:.1f}%' if total_applications > 0 else '0%', table_style)],
        [Paragraph('Отказано', table_style), Paragraph(str(rejected_count), table_style), 
         Paragraph(f'{rejected_count/total_applications*100:.1f}%' if total_applications > 0 else '0%', table_style)],
        [Paragraph('Ручная проверка', table_style), Paragraph(str(manual_count), table_style), 
         Paragraph(f'{manual_count/total_applications*100:.1f}%' if total_applications > 0 else '0%', table_style)],
    ]
    
    decision_table = Table(decision_data, colWidths=[120, 100, 100])
    decision_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, 0), font_name),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('FONTNAME', (0, 1), (-1, -1), font_name),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    story.append(decision_table)
    story.append(Spacer(1, 20))
    
    # Информация о сгенерированном отчете
    story.append(Paragraph(f'Отчет сгенерирован: {timezone.now().strftime("%d.%m.%Y %H:%M:%S")}', 
                          ParagraphStyle('Footer', parent=normal_style, fontSize=8, textColor=colors.grey)))
    
    doc.build(story)
    buffer.seek(0)
    
    return FileResponse(
        buffer,
        as_attachment=True,
        filename=f'report_{date_from.strftime("%Y%m%d")}_{date_to.strftime("%Y%m%d")}.pdf'
    )