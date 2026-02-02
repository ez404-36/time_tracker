from collections import defaultdict

import flet as ft

from apps.time_tracker.consts import ActionIds
from apps.time_tracker.models import PomodoroTimer, ActivityDayTrack, ActivityTrackActionTrackData
from core.state import ActivityTabState


class ActivityTabHelpers:
    def __init__(self, state: ActivityTabState):
        self._state = state

    def refresh_activity_selector_options(self) -> None:
        options = self.get_activity_selector_options()
        selector = self._state['controls']['view']['activity_selector']
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


class TimeTrackDBHelpers:
    def __init__(self, state: ActivityTabState):
        self._state = state

    def get_activity_ids(self) -> list[int]:
        return list(self._state['db']['activities'].keys())

    def refresh_activities(self):
        self._state['db']['activities'] = {
            it.id: it for it in PomodoroTimer.select()
        }

    def get_or_create_activity_track(self) -> ActivityDayTrack:
        day_track = self._state['selected']['day_track']
        if not day_track:
            activity = self._state['selected']['activity']
            day_track = ActivityDayTrack.create(
                activity=activity
            )
            self._state['selected']['day_track'] = day_track
        return day_track

    def get_activity_actions_tracked_time(self) -> dict[str | int, int]:
        activity_track = self._state['selected']['day_track']

        actions_counter = defaultdict(int)

        if activity_track:
            prev_timestamp = None
            prev_action_id = None
            for action_time_data in activity_track.time_track:  # type: ActivityTrackActionTrackData
                application_id = action_time_data['application_id']
                timestamp = action_time_data['timestamp']

                if prev_action_id:
                    if prev_action_id in {ActionIds.PAUSE, ActionIds.STOP}:
                        delta = 0
                    else:
                        delta = timestamp - prev_timestamp
                    actions_counter[prev_action_id] += delta

                prev_timestamp = timestamp
                prev_action_id = application_id

        return actions_counter
