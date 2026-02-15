class ActionIds:
    START = 'start'
    PAUSE = 'pause'
    STOP = 'stop'


class EventType:
    """Тип события"""
    OPEN_APP = 1
    CLOSE_APP = 2
    CHANGE_SETTINGS = 3

    choices = (
        (OPEN_APP, 'Открытие приложения'),
        (CLOSE_APP, 'Закрытие приложения'),
        (CHANGE_SETTINGS, 'Изменение настроек'),
    )


class EventInitiator:
    """Инициатор события"""
    SYSTEM = 1
    USER = 2

    choices = (
        (SYSTEM, 'Система'),
        (USER, 'Пользователь'),
    )
