import flet as ft

from core.di import container
from core.system_events.types import SystemEvent, SystemEventStartMainTracker, SystemEventChangeSettingsData
from ui.base.components.mixins import ShowHideMixin
from ui.consts import Icons, Colors


class TimeTrackingStartButton(ft.IconButton, ShowHideMixin):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._app_settings = container.app_settings
        self._event_bus = container.event_bus

        self.disabled = not any([
            self._app_settings.enable_idle_tracking,
            self._app_settings.enable_window_tracking,
            self._app_settings.enable_pomodoro,
        ])

        self.icon = ft.Icon(
            icon=Icons.START,
            color=self._get_icon_color(),
        )
        self.tooltip = self._get_tooltip()
        self.on_click = self._on_click

        self._event_bus.subscribe('main_tracker.start', self.hide)
        self._event_bus.subscribe('main_tracker.stop', self.show)

        self._event_bus.subscribe('app.change_settings', self.on_event_change_settings)

    async def _on_click(self, e):
        self._event_bus.publish(
            SystemEvent(
                type='main_tracker.start',
                data=SystemEventStartMainTracker(
                    idle_tracking=self._app_settings.enable_idle_tracking,
                    window_tracking=self._app_settings.enable_window_tracking,
                    pomodoro_tracking=self._app_settings.enable_pomodoro,
                )
            )
        )

    def on_event_change_settings(self, data: SystemEventChangeSettingsData):
        tracker_settings = data.values['tracker']

        is_any_tracking_enabled = any([
            tracker_settings.get('enable_window_tracking'),
            tracker_settings.get('enable_idle_tracking'),
            tracker_settings.get('enable_pomodoro'),
        ])

        self.disabled = not is_any_tracking_enabled

        self.icon.color = self._get_icon_color()
        self.tooltip = self._get_tooltip()

        self.update()

    def _get_icon_color(self) -> ft.Colors:
        return Colors.GREEN_LIGHT if not self.disabled else Colors.GREY

    def _get_tooltip(self) -> str:
        return 'Запустить отслеживание активности' if not self.disabled else 'Настройте параметры контроля активности'
