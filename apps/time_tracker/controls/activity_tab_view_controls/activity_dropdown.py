import datetime
from typing import Self

import flet as ft

from apps.time_tracker.controls.activity_tab_view_controls.activity_track_action import ActivityTrackActionControl
from apps.time_tracker.controls.base import BaseActivityTabControl
from apps.time_tracker.models import Action, ActivityTrack
from helpers import ActivityTabHelpers


class ActivityTabActivityDropdown(BaseActivityTabControl):
    """Селектор выбора активности"""

    @property
    def component(self) -> ft.Dropdown:
        return self._state['controls']['view']['activity_selector']

    def build(self) -> Self:
        options = ActivityTabHelpers(self._global_state).get_activity_selector_options()
        disabled = not options

        if disabled:
            label = 'Добавьте активность -->'
            tooltip = 'У вас не добавлено ни одной активности.\nНажмите на кнопку "Добавить активность"'
        else:
            label = 'Чем сегодня займемся?'
            tooltip = None

        self._state['controls']['view']['activity_selector'] = ft.Dropdown(
                editable=True,
                disabled=disabled,
                label=label,
                options=options,
                width=300,
                tooltip=tooltip,
                on_change=self._on_change,
            )

        return self

    def _on_change(self, e):
        val = int(e.control.value)
        activity = self._state['db']['activities'].get(val)

        if activity == self._state['selected']['activity']:
            return

        self._state['selected']['activity'] = activity

        actions_view = self._state['controls']['view']['actions_view']

        existing_activity_track = ActivityTrack.filter(
            activity=activity,
            date=datetime.date.today(),
        ).first()

        self._state['selected']['activity_track'] = existing_activity_track

        # StateDBHelpers(self._global_state).get_activity_actions_tracked_time()
        self._state['controls']['view']['actions_view'].controls.clear()

        for action in activity.actions.order_by(Action.is_target.desc(), Action.is_useful.desc()):
            action_control = ActivityTrackActionControl(self._global_state, action).build()
            actions_view.controls.append(action_control.component)

        actions_view.update()
