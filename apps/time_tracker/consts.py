class ActionIds:
    START = 'start'
    PAUSE = 'pause'
    STOP = 'stop'


class EventType:
    """Тип события"""
    WINDOW_CHANGE = 1
    IDLE_START = 1
    IDLE_END = 3

    choices = (
        (WINDOW_CHANGE, 'Смена активного окна'),
        (IDLE_START, 'Начало бездействия'),
        (IDLE_END, 'Конец бездействия'),
    )


class EventInitiator:
    """Инициатор события"""
    SYSTEM = 1
    USER = 2

    choices = (
        (SYSTEM, 'Система'),
        (USER, 'Пользователь'),
    )
