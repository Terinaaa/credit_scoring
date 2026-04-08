# apps/users/utils.py
def get_menu_by_role(role_name):
    # общий элемент меню для всех пользователей
    base_menu = [
        {'url': '/', 'icon': '🏠', 'text': 'Главная'}
    ]
    
    # пункты меню в зависимости от роли пользователя
    role_menus = {
        None: [
            {'url': '/users/registration/', 'icon': '🔐', 'text': 'Регистрация'},
            {'url': '/users/login/', 'icon': '↪️', 'text': 'Вход'}
        ],
        'credit_manager': [
            {'url': '/credit/', 'icon': '📊', 'text': 'Оценка кредитоспособности'},
            {'url': '/clients/', 'icon': '👤', 'text': 'Данные по клиенту'}
        ],
        'manager': [
            {'url': '/credit/', 'icon': '📊', 'text': 'Оценка кредитоспособности'},
            {'url': '/clients/', 'icon': '👤', 'text': 'Данные по клиенту'},
            {'url': '/reports/', 'icon': '📈', 'text': 'Отчетность'}
        ],
        'db_admin': [
            {'url': '/admin/auth/user/', 'icon': '👥', 'text': 'Управление пользователями'},  # Конкретный URL
            {'url': '/admin/scoring/employmenttype/', 'icon': '💼', 'text': 'Типы занятости'},
            {'url': '/admin/scoring/applicationstatus/', 'icon': '📊', 'text': 'Статусы заявок'},
            {'url': '/admin/scoring/systemdecision/', 'icon': '⚖️', 'text': 'Решения системы'},
            {'url': '/admin/scoring/riskcategory/', 'icon': '⚠️', 'text': 'Категории риска'},
            {'url': '/clients/', 'icon': '👤', 'text': 'Клиенты'},
        ],
        'system_admin': [
            {'url': '/admin/', 'icon': '⚙️', 'text': 'Панель управления'},
            {'url': '/system-admin/', 'icon': '🔧', 'text': 'Управление системой'}
        ]
    }
    
    return base_menu + (role_menus.get(role_name) or role_menus[None])