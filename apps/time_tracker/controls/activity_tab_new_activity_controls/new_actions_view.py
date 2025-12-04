import flet as ft

from apps.time_tracker.controls.activity_tab_new_activity_controls.base import BaseNewActivityModalControl
from apps.time_tracker.controls.activity_tab_new_activity_controls.new_action_row import \
    NewActivityModalActionRowControl
from core.state import State


class NewActivityModalControlActionsView(BaseNewActivityModalControl):
    """
    Компонент действий в модалке создания активности
    """

    def __init__(self, state: State):
        super().__init__(state)

    @property
    def component(self) -> ft.Column:
        return self._state['actions_view']

    def build(self):
        self._state['actions_view'] = ft.Column()
        self._init_add_action_row_button()

    def _init_add_action_row_button(self):
        self._state['add_action_row_button'] = ft.IconButton(
            ft.Icons.ADD,
            on_click=self._on_click_add_action_row_button,
        )

    def _on_click_add_action_row_button(self, e):
        NewActivityModalActionRowControl(self._global_state).build()
