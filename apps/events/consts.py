class EventType:
    """Тип события"""
    OPEN_APP = 1
    CLOSE_APP = 2
    CHANGE_SETTINGS = 3
    UPDATE_PERSISTENT_STORE = 4

    WINDOW_TRACKER_START = 10
    WINDOW_TRACKER_STOP = 11
    WINDOW_TRACKER_SWITCH_WINDOW = 12

    ACTIVITY_TRACKING_START = 20
    ACTIVITY_TRACKING_STOP = 21
    ACTIVITY_TRACKING_DETECT_IDLE = 22
    ACTIVITY_TRACKING_END_IDLE = 23

    ADD_TASK = 30
    DELETE_TASK = 31
    UPDATE_TASK = 32

    POMODORO_CHANGE_STATUS = 40

    # Errors
    WRONG_CONFIG = 100
    FILE_NOT_FOUND = 101
    SYSTEM_ERROR = 102
    APP_ERROR = 103

    choices = (
        (OPEN_APP, 'Открытие приложения'),
        (CLOSE_APP, 'Закрытие приложения'),
        (CHANGE_SETTINGS, 'Изменение настроек'),

        (WINDOW_TRACKER_START, 'Запуск отслеживания активных окон'),
        (WINDOW_TRACKER_STOP, 'Окончание отслеживания активных окон'),
        (WINDOW_TRACKER_SWITCH_WINDOW, 'Изменение активного окна'),

        (ACTIVITY_TRACKING_START, 'Запуск отслеживания активности'),
        (ACTIVITY_TRACKING_STOP, 'Окончание отслеживания активности'),
        (ACTIVITY_TRACKING_DETECT_IDLE, 'Обнаружение бездействия'),
        (ACTIVITY_TRACKING_END_IDLE, 'Окончание бездействия'),

        (ADD_TASK, 'Добавление задачи'),
        (UPDATE_TASK, 'Изменение задачи'),
        (DELETE_TASK, 'Удаление задачи'),

        (POMODORO_CHANGE_STATUS, 'Изменение состояния таймера помодоро'),

        (WRONG_CONFIG, 'Ошибки в конфигурации'),
        (FILE_NOT_FOUND, 'Файл не найден'),
        (SYSTEM_ERROR, 'Системная ошибка'),
        (APP_ERROR, 'Ошибка приложения'),
    )


class EventActor:
    """Инициатор события"""
    SYSTEM = 1
    USER = 2

    choices = (
        (SYSTEM, 'Система'),
        (USER, 'Пользователь'),
    )
