from typing import Self

import flet as ft

from apps.time_tracker.controls.base import BaseActivityTabControl


class ActivityTabNewActivityButtonControl(BaseActivityTabControl):
    @property
    def component(self) -> ft.ElevatedButton:
        return self._state['controls']['view']['new_activity_button']

    def build(self) -> Self:
        self._state['controls']['view']['new_activity_button'] = ft.ElevatedButton(
            'Добавить активность',
            on_click=self._on_click,
        )

        return self

    def _on_click(self, e):
        self._global_state['page'].open(self._state['controls']['new_activity']['modal'])
