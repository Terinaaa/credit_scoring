# apps/users/utils.py
# меню по ролям пользователей
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
            {'url': '/scoring/', 'icon': '📊', 'text': 'Оценка кредитоспособности'},
            {'url': '/clients/', 'icon': '👤', 'text': 'Данные по клиенту'}
        ],
        'manager': [
            {'url': '/scoring/', 'icon': '📊', 'text': 'Оценка кредитоспособности'},
            {'url': '/clients/', 'icon': '👤', 'text': 'Данные по клиенту'},
            {'url': '/reports/', 'icon': '📈', 'text': 'Отчетность'}
        ],
        'db_admin': [
            {'url': '/scoring/', 'icon': '📊', 'text': 'Оценка кредитоспособности'},
            {'url': '/clients/', 'icon': '👤', 'text': 'Данные по клиенту'},
            {'url': '/reports/', 'icon': '📈', 'text': 'Отчетность'}
        ],
        'system_admin': [
            {'url': '/scoring/', 'icon': '📊', 'text': 'Оценка кредитоспособности'},
            {'url': '/clients/', 'icon': '👤', 'text': 'Данные по клиенту'},
            {'url': '/reports/', 'icon': '📈', 'text': 'Отчетность'},
            {'url': '/admin/', 'icon': '📈', 'text': 'Панель управления'}
        ]
    }
    
    return base_menu + (role_menus.get(role_name) or role_menus[None])