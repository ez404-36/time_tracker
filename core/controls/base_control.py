from typing import Self

from core.state import State


class BaseControl:
    def __init__(self, state: State):
        self._global_state = state

    def build(self) -> Self:
        raise NotImplementedError
