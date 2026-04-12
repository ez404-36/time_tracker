import flet as ft

from apps.app_settings.controls.settings_modal import SettingsModal
from core.di import container
from ui.base.components.mixins import ShowHideMixin
from ui.consts import Icons, Colors


class TimeTrackingConfigButton(ft.IconButton, ShowHideMixin):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.icon = ft.Icon(
            icon=Icons.SETTINGS,
            color=Colors.BLUE_LIGHT,
        )
        self.on_click = lambda e: self.page.show_dialog(SettingsModal(mode='tracker'))
        self.tooltip = 'Параметры контроля активности'

        self._event_bus = container.event_bus

        self._event_bus.subscribe('main_tracker.start', self.hide)
        self._event_bus.subscribe('main_tracker.stop', self.show)
