import flet as ft

from models import Action, Activity, ActivityTrackActionTrackData, CONSTS
from state import NewActivityModalState, State, StateDB


class ActivityTabHelpers:
    def __init__(self, state: State):
        self._state = state

    def update_activity_selector_options(self) -> None:
        options = self.get_activity_selector_options()
        selector = self._state['controls']['activity']['activity_tab']['activity_selector']
        if selector:
            selector.options = options
            selector.update()

    def get_activity_selector_options(self) -> list[ft.DropdownOption]:
        return [
            ft.DropdownOption(
                key=it.id,
                content=ft.Text(
                    value=it.title
                ),
                text=it.title,
            )
            for it in self._state['db']['activities'].values()
        ]


class NewActivityModalHelpers:
    def __init__(self, state: NewActivityModalState):
        self._state: NewActivityModalState = state

    def get_selected_action_ids(self) -> list[int]:
        return [
            int(it.controls[0].value)
            for it in self.get_action_row_controls()
        ]

    def get_selected_action_ids_with_target_checkbox(self) -> list[tuple[int, bool]]:
        return [
            (int(it.controls[0].value), it.controls[1].value)
            for it in self.get_action_row_controls()
        ]

    def get_action_row_controls(self):
        return self._state['actions_view'].controls


class StateDBHelpers:
    def __init__(self, state: State):
        self._state: StateDB = state['db']
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
        activity_track = self._global_state['selected']['activity_track']
        activity = self._global_state['selected']['activity']
        actions_rel = activity.actions
        actions = [it.action.id for it in actions_rel] + [CONSTS.PAUSE_ACTION_ID]

        actions_counter = dict.fromkeys(actions, 0)

        if not activity_track:
            return actions_counter

        activity_start = activity_track.start
        prev_timestamp = activity_start
        for action_time_data in activity_track.time_track:  # type: ActivityTrackActionTrackData
            action_id = action_time_data['action_id']
            timestamp = action_time_data['timestamp']

            delta = timestamp - prev_timestamp

            actions_counter[action_id] += delta

            prev_timestamp = timestamp

        return actions_counter
