from typing import Optional

import flet as ft

from apps.time_tracker.models import Action
from core.state import ActivityTabState


class MutateActivityModalActionRowControl(ft.Row):
    def __init__(self, state: ActivityTabState, instance: Optional[Action] = None, **kwargs):
        super().__init__(**kwargs)
        self._state = state
        self._instance = instance

    def build(self, default: str = None):
        def on_click_action_remove(e):
            self.parent.controls.remove(self)
            self.parent.update()

        action_input = ft.TextField(width=200, value=self._instance.title if self._instance else None)
        is_target_action_checkbox = ft.Checkbox(label='Полезное действие', value=self._instance.is_useful if self._instance else None)
        action_delete_button = ft.IconButton(
            ft.Icons.REMOVE,
            on_click=on_click_action_remove,
            visible=not self._instance.is_target if self._instance else True,
        )

        self.controls = [
            action_input,
            is_target_action_checkbox,
            action_delete_button,
        ]
