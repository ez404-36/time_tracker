from typing import Self

import flet as ft
from flet.core.border import Border, BorderSide

from apps.time_tracker.consts import PAUSE_ACTION_ID
from apps.time_tracker.controls.view.action_timer import ActionTimerComponent, \
    ActionTimerStaticComponent
from apps.time_tracker.helpers import ActivityTabHelpers, TimeTrackDBHelpers
from apps.time_tracker.models import Action, ActivityTrack
from core.state import ActivityTabState


class ActivityTrackActionControl(ft.Container):
    def __init__(self, state: ActivityTabState, action: Action, **kwargs):
        kwargs.setdefault('padding', 10)
        super().__init__(**kwargs)
        self._state = state
        self._action = action

        self._action_timer_total_component: ActionTimerStaticComponent | None = None
        self._action_timer_component: ActionTimerComponent | None = None
        self._start_stop_button: ft.IconButton | None = None
        self._is_started = False

    @property
    def action_timer_total(self) -> ActionTimerComponent:
        return self.content.controls[1]

    @property
    def action_timer(self) -> ActionTimerComponent:
        return self.content.controls[3]

    @property
    def action(self) -> Action:
        return self._action

    def get_color(self) -> ft.Colors:
        return ft.Colors.GREEN_300 if self._action.is_useful else ft.Colors.RED_300

    def build(self) -> Self:
        color = self.get_color()

        action_tracked_time = TimeTrackDBHelpers(self._state).get_activity_actions_tracked_time().get(self.action.id, 0)

        self._start_stop_button = ft.IconButton(
            ft.Icons.PLAY_CIRCLE_OUTLINE,
            icon_color=color,
            on_click=self.on_click_start_stop,
        )
        self._action_timer_total_component = ActionTimerStaticComponent(self._action, action_tracked_time)
        self._action_timer_component = ActionTimerComponent(self._action, 0)

        if self._action.is_target:
            font_weight = ft.FontWeight.W_500
        else:
            font_weight = ft.FontWeight.W_400

        self.content = ft.Row(
            controls=[
                ft.Text(
                    self.action.title,
                    size=14,
                    weight=font_weight,
                    color=color,
                    width=120,
                ),
                self._action_timer_total_component,
                self._start_stop_button,
                self._action_timer_component,
            ],
        )

    def on_click_start_stop(self, e):
        if not self._state['selected']['activity_track']:
            activity = self._state['selected']['activity']
            self._state['selected']['activity_track'] = ActivityTrack.create(
                activity=activity
            )

        activity_track = self._state['selected']['activity_track']

        to_update_controls = []

        if not self._is_started:
            for action_control_row in self.parent.controls:
                timer_control: ActionTimerComponent = action_control_row.content.controls[3]
                row_action: Action = timer_control.action
                is_current_row = row_action == self.action

                timer_control.disabled = not is_current_row
                if not is_current_row:
                    timer_control.reset_timer(False)

                to_update_controls.append(timer_control)

                button: ft.IconButton = action_control_row.content.controls[2]
                if is_current_row:
                    button.icon = ft.Icons.PAUSE_CIRCLE_OUTLINE
                else:
                    button.icon = ft.Icons.PLAY_CIRCLE_OUTLINE
                to_update_controls.append(button)

                color = self.get_color()
                if is_current_row:
                    bs = BorderSide(2, color)
                    border = Border(left=bs, top=bs, right=bs, bottom=bs)
                    action_control_row.border = border
                else:
                    action_control_row.border = None
                to_update_controls.append(action_control_row)

            action_id = self._action.id
            self._state['selected']['action'] = self._action
        else:
            action_id = PAUSE_ACTION_ID
            self.action_timer.disabled = True
            self.action_timer.reset_timer()
            self.border = None

            self._start_stop_button.icon = ft.Icons.PLAY_CIRCLE_OUTLINE

            to_update_controls.extend([
                self,
                self._start_stop_button,
            ])

        self.page.update(*to_update_controls)

        activity_track.change_action(action_id)
        self._is_started = not self._is_started

        ActivityTabHelpers(self._state).refresh_activity_actions_total_timers(self.parent)
