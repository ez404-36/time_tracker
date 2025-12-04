from core.controls.base_control import BaseControl
from core.state import ActivityTabState, State


class BaseActivityTabControl(BaseControl):
    def __init__(self, state: State):
        super().__init__(state)
        self._state: ActivityTabState = state['tabs']['activity']
