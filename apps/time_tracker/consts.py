class ActionIds:
    START = 'start'
    PAUSE = 'pause'
    STOP = 'stop'


class EventType:
    """Тип события"""
    OPEN_APP = 1
    CLOSE_APP = 2
    CHANGE_SETTINGS = 3

    # Errors
    WRONG_CONFIG = 100
    FILE_NOT_FOUND = 101

    choices = (
        (OPEN_APP, 'Открытие приложения'),
        (CLOSE_APP, 'Закрытие приложения'),
        (CHANGE_SETTINGS, 'Изменение настроек'),
        (WRONG_CONFIG, 'Ошибки в конфигурации'),
        (FILE_NOT_FOUND, 'Файл найден'),
    )


class EventInitiator:
    """Инициатор события"""
    SYSTEM = 1
    USER = 2

    choices = (
        (SYSTEM, 'Система'),
        (USER, 'Пользователь'),
    )
