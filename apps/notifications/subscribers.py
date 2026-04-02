from apps.notifications.services.audio_notifications import AudioNotificationService
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

    def on_activity_tracker_detect_idle(self, _data: system_event_type.SystemEventTimestampData):
        self._service.play_idle_start_sound()


class SnackbarSubscriber:
    """
    Показывает snackbars в приложении на основе системных событий
    """

    def __init__(self):
        self._event_bus = container.event_bus
        self._app_settings = container.app_settings

        self._event_bus.subscribe('main_tracker.start', self.on_main_tracker_start)
        self._event_bus.subscribe('main_tracker.pause', self.on_main_tracker_pause)
        self._event_bus.subscribe('main_tracker.stop', self.on_main_tracker_stop)

        self._event_bus.subscribe('activity_tracker.detect_idle', self.on_activity_tracker_detect_idle)

        self._event_bus.subscribe('tasks.add', self.on_task_create)
        self._event_bus.subscribe('tasks.update', self.on_task_update)
        self._event_bus.subscribe('tasks.delete', self.on_task_delete)

    @staticmethod
    def on_main_tracker_start(_data: system_event_type.SystemEventTimestampData):
        show_snackbar('Запущено отслеживание активности')

    @staticmethod
    def on_main_tracker_stop(_data: system_event_type.SystemEventTimestampData):
        show_snackbar('Отслеживание активности выключено')

    @staticmethod
    def on_main_tracker_pause(_data: system_event_type.SystemEventTimestampData):
        show_snackbar('Отслеживание активности приостановлено')

    def on_activity_tracker_detect_idle(self, _data: system_event_type.SystemEventTimestampData):
        show_snackbar(f'Обнаружено бездействие более {self._app_settings.idle_threshold} секунд')

    @staticmethod
    def on_task_create(data: system_event_type.SystemEventTaskAction):
        show_snackbar(f'Создана {data.task}')

    @staticmethod
    def on_task_update(data: system_event_type.SystemEventTaskAction):
        show_snackbar(f'{data.task} обновлена')

    @staticmethod
    def on_task_delete(data: system_event_type.SystemEventTaskAction):
        show_snackbar(f'{data.task} удалена')