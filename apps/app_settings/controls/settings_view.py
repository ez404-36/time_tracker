import flet as ft

from core.di import container
from ui.base.components.buttons import SaveButton
from .settings_form import SettingsForm


class SettingsView(ft.Container):
    """
    Таб изменения настроек
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._app_settings = container.app_settings
        self._event_bus = container.event_bus

        self._form: SettingsForm | None = None

    def build(self):
        self._form = SettingsForm(padding=10, in_modal=False, mode='all')

        self.content = ft.Column(
            controls=[
                self._form,
                ft.Container(
                    padding=4,
                ),
                SaveButton(on_click=self._form.save),
            ]
        )
