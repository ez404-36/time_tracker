import time
import datetime
from typing import Self

import flet as ft

from controls.activity_track_controls import ActivityTrackActionControl, ActivityTrackActionsViewControl
from controls.base_control import BaseControl
from helpers import ActivityTabHelpers, StateDBHelpers
from models import ActivityTrack
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

        # self._state['start_button'].disabled = not val
        # self._state['start_button'].update()

        actions_view = self._global_state['controls']['activity']['activity_track']['actions_view']

        existing_activity_track = ActivityTrack.filter(
            activity=activity,
            date=datetime.date.today(),
            stop=None,
        ).first()

        if existing_activity_track:
            self._global_state['selected']['activity_track'] = existing_activity_track

        self._global_state['activity_track_actions_time'] = StateDBHelpers(self._global_state).get_activity_actions_tracked_time()
        self._global_state['controls']['activity']['activity_track']['actions_view'].controls.clear()

        for action in activity.actions:
            action_control = ActivityTrackActionControl(self._global_state, action).init()
            actions_view.controls.append(action_control.component)

        actions_view.update()


# class ActivityTabStartButtonControl(BaseActivityTabControl):
#     """
#     Кнопка "Начать работу".
#     По клику создаёт объект ActivityTrack с текущим выбранным Activity
#     """
#
#     @property
#     def component(self) -> ft.IconButton:
#         return self._state['start_button']
#
#     def init(self) -> Self:
#         self._state['start_button'] = ft.IconButton(
#             ft.Icons.PLAY_CIRCLE,
#             on_click=self._on_click,
#             disabled=True,
#         )
#
#         return self
#
#     def _on_click(self, e):
#         if not self._global_state['selected']['activity_track']:
#             self._global_state['selected']['activity_track'] = ActivityTrack.create(
#                 activity=self._global_state['selected']['activity'],
#             )
#
#         self._state['pause_button'].disabled = False
#         self._state['stop_button'].disabled = False
#
#         self._state['pause_button'].update()
#         self._state['stop_button'].update()

#
# class ActivityTabPauseButtonControl(BaseActivityTabControl):
#     """
#     Кнопка "Приостановить работу".
#     """
#
#     @property
#     def component(self) -> ft.IconButton:
#         return self._state['pause_button']
#
#     def init(self) -> Self:
#         self._state['pause_button'] = ft.IconButton(
#             ft.Icons.PAUSE_CIRCLE,
#             on_click=self._on_click,
#             disabled=True,
#         )
#
#         return self
#
#     def _on_click(self, e):
#         activity_track = self._global_state['selected']['activity_track']
#         activity_track.change_action(CONSTS.PAUSE_ACTION_ID)
#
#         self._state['stop_button'].disabled = True
#         self._state['stop_button'].update()


class ActivityTabStopButtonControl(BaseActivityTabControl):
    @property
    def component(self) -> ft.IconButton:
        return self._state['stop_button']

    def init(self):
        self._state['stop_button'] = ft.IconButton(
            ft.Icons.STOP_CIRCLE,
            on_click=self._on_click,
            disabled=True,
        )

        return self

    def _on_click(self, e):
        activity_track = self._global_state['selected']['activity_track']
        activity_track.stop = int(time.time())
        activity_track.save(only=['stop'])

        self._state['pause_button'].disabled = False
        self._state['stop_button'].disabled = False

        self._state['pause_button'].update()
        self._state['stop_button'].update()


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
        # self._start_button_control: ActivityTabStartButtonControl | None = None
        # self._pause_button_control: ActivityTabPauseButtonControl | None = None
        # self._stop_button_control: ActivityTabStopButtonControl | None = None
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
        # self._start_button_control = ActivityTabStartButtonControl(self._global_state).init()
        # self._pause_button_control = ActivityTabPauseButtonControl(self._global_state).init()
        # self._stop_button_control = ActivityTabStopButtonControl(self._global_state).init()
        self._new_activity_button_control = ActivityTabNewActivityButtonControl(self._global_state).init()
        self._activity_track_control = ActivityTrackActionsViewControl(self._global_state).init()

        target_actions_row = ft.Row(
            [
                self._activity_selector_control.component,
                # self._start_button_control.component,
                # self._pause_button_control.component,
                # self._stop_button_control.component,
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
