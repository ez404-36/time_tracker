import flet as ft

from core.di import container
from ui.base.components.mixins import ShowHideMixin
from ui.consts import Colors, Icons


class TimeTrackerStopButton(ft.IconButton, ShowHideMixin):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.icon = ft.Icon(
            icon=Icons.STOP,
            color=Colors.BLUE_LIGHT,
        )
        self.visible = False
        self.tooltip = 'Выключить отслеживание активности'
        self.on_click = self._on_click

        self._event_bus = container.event_bus
        self._main_tracker = container.main_tracker

        self._event_bus.subscribe('main_tracker.start', self.show)
        self._event_bus.subscribe('main_tracker.stop', self.hide)

    def _on_click(self, e):
        self._main_tracker.stop()
