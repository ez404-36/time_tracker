from typing import Self

import flet as ft

from apps.time_tracker.controls.view.activity_dropdown import ActivityTabActivityDropdown
from apps.time_tracker.controls.view.edit_activity_button import EditActivityButton
from apps.time_tracker.controls.view.new_activity_button import \
    ActivityTabNewActivityButtonControl
from apps.time_tracker.helpers import TimeTrackDBHelpers
from core.state import ActivityTabState, State


class ActivityTabViewControl(ft.Container):
    """Таб активности"""

    def __init__(self, state: State, **kwargs):
        kwargs.setdefault('padding', 20)
        super().__init__(**kwargs)
        self._state: ActivityTabState = state['tabs']['activity']
        self._activity_selector_control: ActivityTabActivityDropdown | None = None
        self._edit_activity_button_control: EditActivityButton | None = None
        self._new_activity_button_control: ActivityTabNewActivityButtonControl | None = None
        self._activity_track_control: ft.Column | None = None

    @property
    def activity_track_component(self) -> ft.Column:
        return self._activity_track_control

    def build(self) -> Self:
        TimeTrackDBHelpers(self._state).refresh_actions()
        TimeTrackDBHelpers(self._state).refresh_activities()

        self._edit_activity_button_control = EditActivityButton(self._state)
        self._activity_selector_control = ActivityTabActivityDropdown(self._state, self._edit_activity_button_control)
        self._state['controls']['view']['activity_selector'] = self._activity_selector_control
        self._new_activity_button_control = ActivityTabNewActivityButtonControl(self._state)
        self._activity_track_control = ft.Column()

        target_actions_row = ft.Row(
            [
                self._activity_selector_control,
                self._edit_activity_button_control,
                self._new_activity_button_control,
            ]
        )

        self.content = ft.Column(
            controls=[
                target_actions_row,
                self.activity_track_component,
            ]
        )
