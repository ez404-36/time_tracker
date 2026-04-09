import flet as ft

from apps.app_settings.controls.settings_form import SettingsForm
from apps.app_settings.controls.types import SettingsFormMode
from core.di import container
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

        self.content = SettingsForm(padding=10, in_modal=True, mode=self._mode)
        self.actions = [
            CancelButton(on_click=self._hide),
            SaveButton(on_click=self._save_settings),
        ]

    def _save_settings(self):
        self.content.save()
        self._hide()

    def _hide(self):
        self.open = False
        self.update()
