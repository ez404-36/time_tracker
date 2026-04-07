import flet as ft

from core.di import container
from core.system_events.types import SystemEvent
from ui.base.components.mixins import ShowHideMixin
from ui.consts import Icons, Colors


class TimeTrackingPomodoroStartWorkButton(ft.IconButton, ShowHideMixin):
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

        self._event_bus.subscribe('main_tracker.start', self.hide)
        self._event_bus.subscribe('main_tracker.pause', self.hide)
        self._event_bus.subscribe('main_tracker.resume', self.hide)
        self._event_bus.subscribe('main_tracker.stop', self.hide)

        self._event_bus.subscribe('pomodoro_tracker.start_work', self.hide)
        self._event_bus.subscribe('pomodoro_tracker.end_work', self.hide)
        self._event_bus.subscribe('pomodoro_tracker.start_rest', self.hide)
        self._event_bus.subscribe('pomodoro_tracker.end_rest', self.show)

    def _on_click(self, e):
        self._event_bus.publish(
            SystemEvent(
                type='pomodoro_tracker.start_work',
            )
        )