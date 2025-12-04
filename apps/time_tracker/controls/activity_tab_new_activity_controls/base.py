import flet as ft

from core.controls.base_control import BaseControl
from core.state import ActivityTabNewActivityModalState, State


class BaseNewActivityModalControl(BaseControl):
    def __init__(self, state: State):
        super().__init__(state)
        self._state: ActivityTabNewActivityModalState = state['tabs']['activity']['controls']['new_activity']
        self._component: ft.Control | None = None
