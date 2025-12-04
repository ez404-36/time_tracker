from typing import Self

import flet as ft

from apps.time_tracker.controls.base import BaseActivityTabControl


class ActivityTrackActionsViewControl(BaseActivityTabControl):
    @property
    def component(self) -> ft.Column:
        return self._state['controls']['view']['actions_view']

    def build(self) -> Self:
        self._state['controls']['view']['actions_view'] = ft.Column()

        return self
