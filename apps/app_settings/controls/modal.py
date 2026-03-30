from dataclasses import asdict

import flet as ft

from apps.app_settings.controls.settings_form import SettingsForm
from apps.app_settings.controls.types import SettingsFormMode
from core.di import container
from core.system_events.types import SystemEvent, SystemEventChangeSettingsData
from ui.base.components.buttons import CancelButton, SaveButton


class SettingsModal(ft.AlertDialog):
    """
    Модальное окно изменения настроек приложения
    """

    content: SettingsForm

    def __init__(self, mode: SettingsFormMode, **kwargs):
        super().__init__(**kwargs)

        self._mode = mode
        self._app_settings = container.app_settings
        self._event_bus = container.event_bus

    def build(self):
        self.modal = True
        self.adaptive = True
        self.title = 'Настройки'

        self.content = SettingsForm(padding=10, mode=self._mode)
        self.actions = [
            CancelButton(on_click=lambda e: self.page.pop_dialog()),
            SaveButton(on_click=self._save_settings),
        ]

    def _save_settings(self, e):
        settings_form_values = asdict(self.content.collect_form_fields())

        for field, value in settings_form_values.items():
            setattr(self._app_settings, field, value)

        self._app_settings.save()

        self._event_bus.publish(
            SystemEvent(
                type='app.change_settings',
                data=SystemEventChangeSettingsData(
                    values=settings_form_values
                )
            )
        )

        self.page.pop_dialog()
