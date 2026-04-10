import flet as ft

from apps.time_tracker.services.main_tracker import MainTracker
from apps.time_tracker.types import PomodoroTimerStatus
from core.di import container
from core.system_events.event_bus import EventBus
from core.system_events.types import SystemEventPomodoroChangeStatus
from ui.base.components.mixins import ShowHideMixin
from ui.consts import Colors, Icons


class TimeTrackingPauseButton(ft.IconButton, ShowHideMixin):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.icon = ft.Icon(
            icon=Icons.PAUSE,
            color=Colors.RED_LIGHT,
        )
        self.tooltip = 'Приостановить отслеживание активности'
        self.visible = False
        self.on_click = self._on_click

        self._event_bus: EventBus = container.event_bus
        self._main_tracker: MainTracker = container.main_tracker

        self._event_bus.subscribe('main_tracker.start', self.show)
        self._event_bus.subscribe('main_tracker.pause', self.hide)
        self._event_bus.subscribe('main_tracker.resume', self.show)
        self._event_bus.subscribe('main_tracker.stop', self.hide)

        self._event_bus.subscribe('pomodoro_tracker.change_status', self.on_pomodoro_tracker_change_status)

    def _on_click(self, e):
        self._main_tracker.pause()

    def on_pomodoro_tracker_change_status(self, data: SystemEventPomodoroChangeStatus):
        new_status: PomodoroTimerStatus = data.new_status

        if new_status in ['working', 'resting']:
            self.show()
        else:
            self.hide()
