from dataclasses import asdict

import flet as ft

from apps.settings.controls.settings_form import SettingsForm
from apps.time_tracker.consts import EventType, EventInitiator
from apps.time_tracker.models import Event
from core.settings import AppSettings
from ui.base.components.buttons import CancelButton, SaveButton


class SettingsModal(ft.AlertDialog):
    content: SettingsForm

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._app_settings = AppSettings.get_solo()

    def build(self):
        self.modal = True
        self.adaptive = True
        self.title = 'Настройки'

        self.content = SettingsForm(self._app_settings)
        self.actions = [
            CancelButton(on_click=lambda e: self.page.pop_dialog()),
            SaveButton(on_click=self._save_settings),
        ]

    def _save_settings(self, e):
        settings_form_values = asdict(self.content.collect_form_fields())
        for field, value in settings_form_values.items():
            setattr(self._app_settings, field, value)
        self._app_settings.save()
        Event.create(type=EventType.CHANGE_SETTINGS, initiator=EventInitiator.USER, data=settings_form_values)
        self.page.pop_dialog()
