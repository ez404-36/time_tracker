import flet as ft

from apps.time_tracker.controls.mutate_modal.modal import MutateActivityModalControl
from core.state import ActivityTabState


class ActivityTabNewActivityButtonControl(ft.ElevatedButton):
    def __init__(self, state: ActivityTabState, **kwargs):
        kwargs.setdefault('text', 'Добавить активность')
        super().__init__(**kwargs)
        self._state = state

    def build(self):
        self.on_click = self._on_click

    def _on_click(self, e):
        modal = MutateActivityModalControl(self._state)
        self.page.open(modal)
