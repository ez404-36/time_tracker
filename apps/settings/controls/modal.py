from typing import Callable

import flet as ft

from apps.settings.controls.panel import SettingsPanel
from apps.time_tracker.consts import EventType, EventInitiator
from apps.time_tracker.models import Event
from core.settings import app_settings


class SettingsModal(ft.AlertDialog):
    content: SettingsPanel

    def __init__(self, on_close: Callable[[], None], **kwargs):
        kwargs.update(
            dict(
                modal=True,
                adaptive=True,
                title=ft.Text("Настройки"),
            )
        )
        super().__init__(**kwargs)

        self._on_close = on_close
        self._app_settings = app_settings

    def build(self):
        self.content = SettingsPanel(self._app_settings)
        self.actions = [
            ft.TextButton('Отмена', on_click=lambda e: self._on_close()),
            ft.TextButton('Сохранить', on_click=self._save_settings)
        ]

    def _save_settings(self, e):
        settings_form_values = self.content.collect_form_fields()
        for field, value in settings_form_values.items():
            setattr(self._app_settings, field, value)
        self._app_settings.save()
        Event.create(type=EventType.CHANGE_SETTINGS, initiator=EventInitiator.USER, data=settings_form_values)
        self._on_close()