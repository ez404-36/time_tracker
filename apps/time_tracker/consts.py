class ActionIds:
    START = 'start'
    PAUSE = 'pause'
    STOP = 'stop'


class EventType:
    WINDOW_CHANGE = 1
    IDLE_START = 1
    IDLE_END = 3

    choices = (
        (WINDOW_CHANGE, 'Смена активного окна'),
        (IDLE_START, 'Начало бездействия'),
        (IDLE_END, 'Конец бездействия'),
    )
