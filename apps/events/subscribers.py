from dataclasses import asdict

from apps.events.consts import EventActor, EventType
from apps.events.models import Event
from core.di import container
from core.system_events import types as system_event_type
from ui.utils import show_snackbar


class EventsSubscriber:
    """
    Создаёт системные ивенты
    """

    def __init__(self):
        self._event_bus = container.event_bus

        self._event_bus.subscribe('app.open', self.on_app_open)
        self._event_bus.subscribe('app.close', self.on_app_close)
        self._event_bus.subscribe('app.change_settings', self.on_app_change_settings)
        self._event_bus.subscribe('app.wrong_config', self.on_app_wrong_config)
        self._event_bus.subscribe('app.file_not_found', self.on_app_file_not_found)

        self._event_bus.subscribe('tracker.start', self.on_tracker_start)
        self._event_bus.subscribe('tracker.stop', self.on_tracker_stop)
        self._event_bus.subscribe('tracker.switch_window', self.on_tracker_switch_window)
        self._event_bus.subscribe('tracker.detect_idle', self.on_tracker_detect_idle)
        self._event_bus.subscribe('tracker.stop_idle', self.on_tracker_stop_idle)

        self._event_bus.subscribe('tasks.add', self.on_task_create)
        self._event_bus.subscribe('tasks.update', self.on_task_update)

    @staticmethod
    def on_app_open(data: system_event_type.SystemEventTimestampData):
        Event.create(
            type=EventType.OPEN_APP,
            actor=EventActor.USER,
            ts=data.ts,
        )

    @staticmethod
    def on_app_close(data: system_event_type.SystemEventTimestampData):
        Event.create(
            type=EventType.CLOSE_APP,
            actor=EventActor.USER,
            ts=data.ts,
        )

    @staticmethod
    def on_app_change_settings(data: system_event_type.SystemEventChangeSettingsData):
        Event.create(
            type=EventType.CLOSE_APP,
            actor=EventActor.USER,
            data=data.values,
        )

    @staticmethod
    def on_app_wrong_config(data: system_event_type.SystemEventWrongConfigData):
        Event.create(
            type=EventType.WRONG_CONFIG,
            actor=EventActor.SYSTEM,
            data=asdict(data),
        )

    @staticmethod
    def on_app_file_not_found(data: system_event_type.SystemEventFileNotFound):
        Event.create(
            type=EventType.FILE_NOT_FOUND,
            actor=EventActor.SYSTEM,
            data=asdict(data),
        )

    @staticmethod
    def on_tracker_switch_window(data: system_event_type.SystemEventSwitchWindowData):
        Event.create(
            type=EventType.SWITCH_WINDOW,
            actor=EventActor.USER,
            ts=data.ts,
            data=data.window,
        )

    @staticmethod
    def on_tracker_start(data: system_event_type.SystemEventTimestampData):
        show_snackbar('Запущено отслеживание активности')
        Event.create(
            type=EventType.START_TRACKING,
            actor=EventActor.USER,
            ts=data.ts,
        )

    @staticmethod
    def on_tracker_stop(data: system_event_type.SystemEventTimestampData):
        show_snackbar('Отслеживание активности остановлено')
        Event.create(
            type=EventType.STOP_TRACKING,
            actor=EventActor.USER,
            ts=data.ts,
        )

    @staticmethod
    def on_tracker_detect_idle(data: system_event_type.SystemEventTimestampData):
        Event.create(
            type=EventType.DETECT_IDLE,
            actor=EventActor.SYSTEM,
            ts=data.ts,
        )

    @staticmethod
    def on_tracker_stop_idle(data: system_event_type.SystemEventTimestampData):
        Event.create(
            type=EventType.END_IDLE,
            actor=EventActor.SYSTEM,
            ts=data.ts,
        )

    @staticmethod
    def on_task_create(data: system_event_type.SystemEventTaskAction):
        show_snackbar(f'Создана {data.task}')
        Event.create(
            type=EventType.ADD_TASK,
            actor=EventActor.USER,
            data=asdict(data),
        )

    @staticmethod
    def on_task_update(data: system_event_type.SystemEventTaskAction):
        show_snackbar(f'{data.task} обновлена')
        Event.create(
            type=EventType.UPDATE_TASK,
            actor=EventActor.USER,
            data=asdict(data),
        )

    @staticmethod
    def on_task_delete(data: system_event_type.SystemEventTaskAction):
        show_snackbar(f'{data.task} удалена')
        Event.create(
            type=EventType.DELETE_TASK,
            actor=EventActor.USER,
            data=asdict(data),
        )
