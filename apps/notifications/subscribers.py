from apps.notifications.services.audio_notifications import AudioNotificationService
from apps.time_tracker.types import PomodoroTimerStatus
from core.di import container
from core.system_events import types as system_event_type
from ui.utils import show_snackbar


class AudioNotificationSubscriber:
    """
    Отправляет звуковые уведомления в приложении на основе системных событий
    """

    def __init__(self):
        self._event_bus = container.event_bus
        self._service = AudioNotificationService()

        self._event_bus.subscribe('activity_tracker.detect_idle', self.on_activity_tracker_detect_idle)
        self._event_bus.subscribe('pomodoro_tracker.change_status', self.on_pomodoro_tracker_change_status)

    def on_activity_tracker_detect_idle(self, _data: system_event_type.SystemEventTimestampData):
        self._service.play_idle_start_sound()

    def on_pomodoro_tracker_change_status(self, data: system_event_type.SystemEventPomodoroChangeStatus):
        new_status = data.new_status

        if new_status in ['working_stop', 'resting_stop']:
            self._service.play_pomodoro_sound()


class SnackbarSubscriber:
    """
    Показывает snackbars в приложении на основе системных событий
    """

    def __init__(self):
        self._event_bus = container.event_bus
        self._app_settings = container.app_settings

        self._event_bus.subscribe('app.change_settings', self.on_change_settings)

        self._event_bus.subscribe('media.add_file', self.on_add_custom_file)
        self._event_bus.subscribe('media.delete_file', self.on_delete_custom_file)

        self._event_bus.subscribe('main_tracker.start', self.on_main_tracker_start)
        self._event_bus.subscribe('main_tracker.pause', self.on_main_tracker_pause)
        self._event_bus.subscribe('main_tracker.resume', self.on_main_tracker_resume)
        self._event_bus.subscribe('main_tracker.stop', self.on_main_tracker_stop)

        self._event_bus.subscribe('activity_tracker.detect_idle', self.on_activity_tracker_detect_idle)
        self._event_bus.subscribe('pomodoro_tracker.change_status', self.on_pomodoro_tracker_change_status)

        self._event_bus.subscribe('tasks.add', self.on_task_create)
        self._event_bus.subscribe('tasks.update', self.on_task_update)
        self._event_bus.subscribe('tasks.delete', self.on_task_delete)

        self._event_bus.subscribe('error.system', self.on_app_system_error)

    @staticmethod
    def on_change_settings(_data: system_event_type.SystemEventChangeSettingsData):
        show_snackbar('Настройки успешно изменены')

    @staticmethod
    def on_main_tracker_start(_data: system_event_type.SystemEventTimestampData):
        show_snackbar('Запущено отслеживание активности')

    @staticmethod
    def on_main_tracker_stop(_data: system_event_type.SystemEventTimestampData):
        show_snackbar('Отслеживание активности выключено')

    @staticmethod
    def on_main_tracker_pause(_data: system_event_type.SystemEventTimestampData):
        show_snackbar('Отслеживание активности приостановлено')

    @staticmethod
    def on_main_tracker_resume(_data: system_event_type.SystemEventTimestampData):
        show_snackbar('Отслеживание активности возобновлено')

    def on_activity_tracker_detect_idle(self, _data: system_event_type.SystemEventTimestampData):
        show_snackbar(f'Обнаружено бездействие более {self._app_settings.idle_threshold} секунд')

    @staticmethod
    def on_pomodoro_tracker_change_status(data: system_event_type.SystemEventPomodoroChangeStatus):
        new_status: PomodoroTimerStatus = data.new_status

        if new_status == 'working_stop':
            show_snackbar('Пора отдохнуть')
        elif new_status == 'resting_stop':
            show_snackbar('Пора работать')

    @staticmethod
    def on_task_create(data: system_event_type.SystemEventTaskAction):
        show_snackbar(f'Создана {data.task}')

    @staticmethod
    def on_task_update(data: system_event_type.SystemEventTaskAction):
        show_snackbar(f'{data.task} обновлена')

    @staticmethod
    def on_task_delete(data: system_event_type.SystemEventTaskAction):
        show_snackbar(f'{data.task} удалена')

    @staticmethod
    def on_app_system_error(data: system_event_type.SystemEventAppError):
        show_snackbar(f'ОШИБКА в {data.source}: {data.error}')

    @staticmethod
    def on_add_custom_file(data: system_event_type.SystemEventFileInfo):
        show_snackbar(f'Файл {data.filename} успешно добавлен')

    @staticmethod
    def on_delete_custom_file(data: system_event_type.SystemEventFileInfo):
        show_snackbar(f'Файл {data.filename} удалён')
