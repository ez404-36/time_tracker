from typing import Self

from state import State


class BaseControl:
    def __init__(self, state: State):
        self._global_state = state

    def init(self) -> Self:
        raise NotImplementedError
