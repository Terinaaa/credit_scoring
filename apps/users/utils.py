# apps/users/utils.py
def get_menu_by_role(role_name):
    # общий элемент меню для всех пользователей
    base_menu = [
        {'url': '/', 'text': 'Главная'}
    ]
    
    # пункты меню в зависимости от роли пользователя
    role_menus = {
        None: [
            {'url': '/users/registration/', 'icon': '🔐', 'text': 'Регистрация'},
            {'url': '/users/login/', 'icon': '↪️', 'text': 'Вход'}
        ],
        'credit_manager': [
            {'url': '/credit/', 'text': 'Оценка кредитоспособности'},
            {'url': '/clients/', 'text': 'Данные по клиенту'}
        ],
        'manager': [
            {'url': '/credit/', 'text': 'Оценка кредитоспособности'},
            {'url': '/clients/', 'text': 'Данные по клиенту'},
            {'url': '/reports/', 'text': 'Отчетность'}
        ],
        'db_admin': [
            {'url': '/admin/auth/user/',  'text': 'Управление пользователями'},  # Конкретный URL
            {'url': '/admin/scoring/employmenttype/','text': 'Типы занятости'},
            {'url': '/admin/scoring/applicationstatus/', 'text': 'Статусы заявок'},
            {'url': '/admin/scoring/systemdecision/', 'text': 'Решения системы'},
            {'url': '/admin/scoring/riskcategory/', 'text': 'Категории риска'},
            {'url': '/clients/', 'text': 'Клиенты'},
        ],
        'system_admin': [
            {'url': '/admin/', 'icon': '⚙️', 'text': 'Панель управления'},
            {'url': '/system-admin/', 'icon': '🔧', 'text': 'Управление системой'}
        ]
    }
    
    return base_menu + (role_menus.get(role_name) or role_menus[None])