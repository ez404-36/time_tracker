from dataclasses import asdict

import flet as ft

from apps.app_settings.controls.settings_form import SettingsForm
from apps.events.models import Event
from apps.events.consts import EventActor, EventType
from core.di import container
from ui.base.components.buttons import SaveButton
from ui.utils import show_snackbar


class SettingsView(ft.Container):
    """
    Таб изменения настроек
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._app_settings = container.app_settings

        self._form: SettingsForm | None = None


    def build(self):
        self._form = SettingsForm(padding=10, in_modal=False, mode='all')

        self.content = ft.Column(
            controls=[
                self._form,
                ft.Container(
                    padding=4,
                ),
                SaveButton(on_click=self._save_settings),
            ]
        )

    def _save_settings(self, e):
        settings_form_values = asdict(self._form.collect_form_fields())

        for values in settings_form_values.values():
            if values is None:
                continue

            for field, value in values.items():
                setattr(self._app_settings, field, value)

        self._app_settings.save()

        Event.create(type=EventType.CHANGE_SETTINGS, actor=EventActor.USER, data=settings_form_values)

        show_snackbar('Настройки изменены')
