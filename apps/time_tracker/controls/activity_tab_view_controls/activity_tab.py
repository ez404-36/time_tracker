from typing import Self

import flet as ft

from apps.time_tracker.controls.activity_tab_view_controls.activity_dropdown import ActivityTabActivityDropdown
from apps.time_tracker.controls.activity_tab_view_controls.activity_track_actions_view import \
    ActivityTrackActionsViewControl
from apps.time_tracker.controls.activity_tab_view_controls.new_activity_button import \
    ActivityTabNewActivityButtonControl
from apps.time_tracker.controls.base import BaseActivityTabControl
from apps.time_tracker.helpers import StateDBHelpers
from core.state import State


class ActivityTabControl(BaseActivityTabControl):
    """Таб активности"""

    def __init__(self, state: State):
        super().__init__(state)
        self._activity_selector_control: ActivityTabActivityDropdown | None = None
        self._new_activity_button_control: ActivityTabNewActivityButtonControl | None = None
        self._activity_track_control: ActivityTrackActionsViewControl | None = None

    @property
    def component(self) -> ft.Container:
        return self._state['controls']['view']['tab']

    @property
    def activity_track_component(self) -> ft.Column:
        return self._activity_track_control.component

    def build(self) -> Self:
        StateDBHelpers(self._global_state).refresh_actions()
        StateDBHelpers(self._global_state).refresh_activities()

        self._activity_selector_control = ActivityTabActivityDropdown(self._global_state).build()
        self._new_activity_button_control = ActivityTabNewActivityButtonControl(self._global_state).build()
        self._activity_track_control = ActivityTrackActionsViewControl(self._global_state).build()

        target_actions_row = ft.Row(
            [
                self._activity_selector_control.component,
                self._new_activity_button_control.component,
            ]
        )

        self._state['controls']['view']['tab'] = ft.Container(
            padding=20,
            content=ft.Column(
                controls=[
                    target_actions_row,
                    self.activity_track_component,
                ]
            )
        )

        return self
