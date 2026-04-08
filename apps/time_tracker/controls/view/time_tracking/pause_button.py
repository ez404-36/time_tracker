import flet as ft

from apps.time_tracker.services.main_tracker import MainTracker
from core.di import container
from core.system_events.event_bus import EventBus
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

        self._event_bus.subscribe('pomodoro_tracker.end_work', self.hide)
        self._event_bus.subscribe('pomodoro_tracker.end_rest', self.hide)

    def _on_click(self, e):
        self._main_tracker.pause()
