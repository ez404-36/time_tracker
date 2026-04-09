import flet as ft

from apps.time_tracker.types import PomodoroTimerStatus
from core.di import container
from core.system_events import types as system_event_type
from ui.base.components.mixins import ShowHideMixin
from ui.consts import Icons, Colors


class TimeTrackingPomodoroStartRestButton(ft.IconButton, ShowHideMixin):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.icon = ft.Icon(
            icon=Icons.START,
            color=Colors.GREEN_LIGHT,
        )
        self.tooltip = 'Начать'
        self.visible = False
        self.on_click = self._on_click

        self._app_settings = container.app_settings
        self._event_bus = container.event_bus
        self._main_tracker = container.main_tracker

        self._event_bus.subscribe('pomodoro_tracker.change_status', self.on_pomodoro_tracker_change_status)

    def _on_click(self):
        self._main_tracker.pomodoro_tracker.start_next_timer()

    def on_pomodoro_tracker_change_status(self, data: system_event_type.SystemEventPomodoroChangeStatus):
        new_status: PomodoroTimerStatus = data.new_status

        if new_status == 'working_stop':
            self.show()
        else:
            self.hide()
