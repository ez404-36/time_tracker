import flet as ft

from core.di import container
from core.system_events.types import SystemEvent
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

        self._event_bus.subscribe('main_tracker.start', self.show)
        self._event_bus.subscribe('main_tracker.stop', self.hide)

    def _on_click(self, e):
        self._event_bus.publish(
            SystemEvent(
                type='main_tracker.stop',
            )
        )
