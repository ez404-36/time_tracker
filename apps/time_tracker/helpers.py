from collections import defaultdict

import flet as ft

from apps.time_tracker.consts import PAUSE_ACTION_ID, STOP_ACTION_ID
from apps.time_tracker.models import Action, Activity, ActivityTrackActionTrackData
from core.state import ActivityTabDBState, ActivityTabNewActivityModalState, State


class ActivityTabHelpers:
    def __init__(self, state: State):
        self._state = state

    def refresh_activity_selector_options(self) -> None:
        options = self.get_activity_selector_options()
        selector = self._state['tabs']['activity']['controls']['view']['activity_selector']
        if selector:
            selector.options = options
            selector.update()

    def refresh_activity_actions_total_timers(self) -> None:
        tracked_time = StateDBHelpers(self._state).get_activity_actions_tracked_time()
        for action_control_row in self._state['tabs']['activity']['controls']['view']['actions_view'].controls:
            total_timer_control = action_control_row.content.controls[1]
            action = total_timer_control.action
            action_tracked_time = tracked_time.get(action.id, 0)
            total_timer_control.seconds = action_tracked_time
            total_timer_control.update_value()


    def get_activity_selector_options(self) -> list[ft.DropdownOption]:
        return [
            ft.DropdownOption(
                key=it.id,
                content=ft.Text(
                    value=it.title
                ),
                text=it.title,
            )
            for it in self._state['tabs']['activity']['db']['activities'].values()
        ]


class NewActivityModalHelpers:
    def __init__(self, state: ActivityTabNewActivityModalState):
        self._state: ActivityTabNewActivityModalState = state

    def get_actions_with_useful_checkbox(self) -> list[tuple[str, bool]]:
        return [
            (it.controls[0].value, it.controls[1].value)
            for it in self.get_action_row_controls()
        ]

    def get_action_row_controls(self):
        return self._state['actions_view'].controls


# TODO: стейт должен быть не полный, а только для таба активности
class StateDBHelpers:
    def __init__(self, state: State):
        self._state: ActivityTabDBState = state['tabs']['activity']['db']
        self._global_state = state

    def get_action_ids(self) -> list[int]:
        return list(self._state['actions'].keys())

    def get_activity_ids(self) -> list[int]:
        return list(self._state['activities'].keys())

    def refresh_actions(self):
        self._state['actions'] = {
            it.id: it for it in Action.select()
        }

    def refresh_activities(self):
        self._state['activities'] = {
            it.id: it for it in Activity.select()
        }

    def get_activity_actions_tracked_time(self) -> dict[str | int, int]:
        activity_track = self._global_state['tabs']['activity']['selected']['activity_track']

        actions_counter = defaultdict(int)

        if activity_track:
            prev_timestamp = None
            prev_action_id = None
            for action_time_data in activity_track.time_track:  # type: ActivityTrackActionTrackData
                action_id = action_time_data['action_id']
                timestamp = action_time_data['timestamp']

                if prev_action_id:
                    if prev_action_id in {PAUSE_ACTION_ID, STOP_ACTION_ID}:
                        delta = 0
                    else:
                        delta = timestamp - prev_timestamp
                    actions_counter[prev_action_id] += delta

                prev_timestamp = timestamp
                prev_action_id = action_id

        return actions_counter
