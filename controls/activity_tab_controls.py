import datetime
from typing import Self

import flet as ft

from controls.activity_track_controls import ActivityTrackActionControl, ActivityTrackActionsViewControl
from controls.base_control import BaseControl
from helpers import ActivityTabHelpers, StateDBHelpers
from models import Action, ActivityTrack
from state import ActivityTabState, State


class BaseActivityTabControl(BaseControl):
    def __init__(self, state: State):
        super().__init__(state)
        self._state: ActivityTabState = state['controls']['activity']['activity_tab']


class ActivityTabActivitySelectorControl(BaseActivityTabControl):
    """Селектор выбора активности"""

    @property
    def component(self) -> ft.Dropdown:
        return self._state['activity_selector']

    def init(self) -> Self:
        options = ActivityTabHelpers(self._global_state).get_activity_selector_options()
        disabled = not options

        if disabled:
            label = 'Добавьте активность -->'
            tooltip = 'У вас не добавлено ни одной активности.\nНажмите на кнопку "Добавить активность"'
        else:
            label = 'Чем сегодня займемся?'
            tooltip = None

        self._state['activity_selector'] = ft.Dropdown(
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
        activity = self._global_state['db']['activities'].get(val)

        if activity == self._global_state['selected']['activity']:
            return

        self._global_state['selected']['activity'] = activity

        actions_view = self._global_state['controls']['activity']['activity_track']['actions_view']

        existing_activity_track = ActivityTrack.filter(
            activity=activity,
            date=datetime.date.today(),
        ).first()

        self._global_state['selected']['activity_track'] = existing_activity_track

        StateDBHelpers(self._global_state).refresh_activity_actions_tracked_time()
        self._global_state['controls']['activity']['activity_track']['actions_view'].controls.clear()

        for action in activity.actions.order_by(Action.is_target.desc(), Action.is_useful.desc()):
            action_control = ActivityTrackActionControl(self._global_state, action).init()
            actions_view.controls.append(action_control.component)

        actions_view.update()


class ActivityTabNewActivityButtonControl(BaseActivityTabControl):
    @property
    def component(self) -> ft.ElevatedButton:
        return self._state['new_activity_button']

    def init(self) -> Self:
        self._state['new_activity_button'] = ft.ElevatedButton(
            'Добавить активность',
            on_click=self._on_click,
        )

        return self

    def _on_click(self, e):
        self._global_state['page'].open(self._global_state['controls']['activity']['new_activity_modal']['modal'])


class ActivityTabControl(BaseActivityTabControl):
    """Таб активности"""

    def __init__(self, state: State):
        super().__init__(state)
        self._activity_selector_control: ActivityTabActivitySelectorControl | None = None
        self._new_activity_button_control: ActivityTabNewActivityButtonControl | None = None
        self._activity_track_control: ActivityTrackActionsViewControl | None = None

    @property
    def component(self) -> ft.Column:
        return self._state['tab']

    @property
    def activity_track_component(self) -> ft.Column:
        return self._activity_track_control.component

    def init(self) -> Self:
        self._activity_selector_control = ActivityTabActivitySelectorControl(self._global_state).init()
        self._new_activity_button_control = ActivityTabNewActivityButtonControl(self._global_state).init()
        self._activity_track_control = ActivityTrackActionsViewControl(self._global_state).init()

        target_actions_row = ft.Row(
            [
                self._activity_selector_control.component,
                self._new_activity_button_control.component,
            ]
        )

        self._state['tab'] = ft.Column(
            controls=[
                ft.Row(controls=[ft.Text('Трекер времени', size=30)]),
                target_actions_row,
            ]
        )

        return self
