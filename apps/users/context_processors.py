# apps/users/context_processors.py
from .utils import get_menu_by_role

def menu_context(request):
    """Добавляет пункты меню в контекст всех шаблонов"""
    menu_items = [] # пустой список для пунктов меню
    
    if hasattr(request, 'user') and request.user.is_authenticated: # есть ли в запросе объект пользователя и авторизован ли он 
        # получение роли, если она есть и заполнена
        role_name = request.user.role.name if hasattr(request.user, 'role') and request.user.role else None 
        # вызов функции для получения элементов меню по роли
        menu_items = get_menu_by_role(role_name)
    # если неавторизован, то получение элементов меню для "Гостя"
    else:
        menu_items = get_menu_by_role(None)
    return {'menu_items': menu_items} # возврат словаря