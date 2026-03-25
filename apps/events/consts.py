class EventType:
    """Тип события"""
    OPEN_APP = 1
    CLOSE_APP = 2
    CHANGE_SETTINGS = 3

    SWITCH_WINDOW = 4
    DETECT_IDLE = 5
    END_IDLE = 6

    START_TRACKING = 10
    STOP_TRACKING = 11

    ADD_TASK = 20
    UPDATE_TASK = 21
    REMOVE_TASK = 22

    POMODORO_CHANGE_STATUS = 30

    # Errors
    WRONG_CONFIG = 100
    FILE_NOT_FOUND = 101
    SYSTEM_ERROR = 102
    APP_ERROR = 103

    choices = (
        (OPEN_APP, 'Открытие приложения'),
        (CLOSE_APP, 'Закрытие приложения'),
        (CHANGE_SETTINGS, 'Изменение настроек'),

        (SWITCH_WINDOW, 'Изменение активного окна'),
        (DETECT_IDLE, 'Обнаружение бездействия'),
        (END_IDLE, 'Окончание бездействия'),

        (START_TRACKING, 'Запуск отслеживания активности'),
        (STOP_TRACKING, 'Окончание отслеживания активности'),

        (ADD_TASK, 'Добавление задачи'),
        (UPDATE_TASK, 'Изменение задачи'),
        (REMOVE_TASK, 'Удаление задачи'),

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
