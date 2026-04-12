from typing import TYPE_CHECKING

from core.system_events.types import SystemEvent, SystemEventChangeSettingsData, SystemEventStartMainTracker

from .idle_tracker import IdleTracker
from .pomodoro_tracker import PomodoroTracker
from .window_tracker import WindowTracker

if TYPE_CHECKING:
    from apps.app_settings.models import AppSettings
    from core.store import SessionStore
    from core.system_events.event_bus import EventBus


class MainTracker:
    """
    Отвечает за работу всех трекеров:
    - активных окон
    - бездействия
    - таймера помодоро
    """

    def __init__(self, event_bus: 'EventBus', app_settings: 'AppSettings', session_store: 'SessionStore'):
        self.running = False
        self.paused = False

        self.params = SystemEventStartMainTracker(
            idle_tracking=app_settings.enable_idle_tracking,
            window_tracking=app_settings.enable_window_tracking,
            pomodoro_tracking=app_settings.enable_pomodoro,
        )

        self.window_tracker = WindowTracker(event_bus=event_bus, session_store=session_store)
        self.activity_tracker = IdleTracker(event_bus=event_bus, app_settings=app_settings)
        self.pomodoro_tracker = PomodoroTracker(event_bus=event_bus, app_settings=app_settings)

        self._event_bus = event_bus
        self._app_settings = app_settings

        self._event_bus.subscribe('app.change_settings', self._on_event_change_settings)

    def start(self):
        if self.running:
            return

        self.running = True

        self._event_bus.publish(
            SystemEvent(
                type='main_tracker.start',
                data=self.params
            )
        )

    def stop(self):
        if not self.running:
            return

        self.running = False

        self._event_bus.publish(
            SystemEvent(
                type='main_tracker.stop',
            )
        )

    def pause(self):
        """
        Ручная приостановка трекера
        """

        if not self.running:
            return

        self.paused = True
        self._event_bus.publish(
            SystemEvent(
                type='main_tracker.pause',
            )
        )

    def hold(self):
        """
        Автоматическая приостановка трекера.
        Ожидание действий от пользователя
        """

        if not self.running:
            return

        self.paused = True
        self._event_bus.publish(
            SystemEvent(
                type='main_tracker.hold',
            )
        )

    def resume(self):
        if not self.paused:
            return

        self.paused = False
        self._event_bus.publish(
            SystemEvent(
                type='main_tracker.resume',
            )
        )

    def _on_event_change_settings(self, data: SystemEventChangeSettingsData):
        tracker_settings = data.values['tracker']

        self.params = SystemEventStartMainTracker(
            window_tracking=tracker_settings.get('enable_window_tracking', self._app_settings.enable_window_tracking),
            idle_tracking=tracker_settings.get('enable_idle_tracking', self._app_settings.enable_idle_tracking),
            pomodoro_tracking=tracker_settings.get('enable_pomodoro', self._app_settings.enable_pomodoro),
        )

