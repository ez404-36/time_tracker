import flet as ft

from apps.time_tracker.controls.mutate_modal.modal import MutateActivityModalControl
from core.state import ActivityTabState


class EditActivityButton(ft.IconButton):
    def __init__(self, state: ActivityTabState, **kwargs):
        kwargs.setdefault('tooltip', 'Редактировать активность')
        kwargs.setdefault('icon', ft.Icons.EDIT)
        kwargs.setdefault('visible', False)
        super().__init__(**kwargs)
        self._state = state

    def build(self):
        self.on_click = self._on_click

    def _on_click(self, e):
        modal = MutateActivityModalControl(self._state, self._state['selected']['activity'])
        self.page.open(modal)
