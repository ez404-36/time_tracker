import asyncio
import datetime
from typing import Self

import flet as ft
from flet.core.border import Border, BorderSide

from controls.base_control import BaseControl
from helpers import ActivityTabHelpers
from models import Action, ActivityActions, ActivityTrack, CONSTS
from state import ActivityTabActivityTrackState, State


class BaseActivityTabActivityTrackControl(BaseControl):
    def __init__(self, state: State):
        super().__init__(state)
        self._state: ActivityTabActivityTrackState = state['controls']['activity']['activity_track']



class ActionTimerComponent(ft.Text):
    def __init__(self, action_relation: ActivityActions, seconds: int, **kwargs):
        super().__init__(**kwargs)
        self.running = False
        self.disabled = True
        self.seconds = seconds
        self._action_relation = action_relation

    @property
    def action(self) -> Action:
        return self._action_relation.action

    def did_mount(self):
        self.running = True
        self.page.run_task(self.update_timer)
        self.update_value()

    def will_unmount(self):
        self.running = False

    def update_value(self, with_refresh=True):
        if self.seconds:
            self.value = datetime.timedelta(seconds=self.seconds)
        else:
            self.value = None

        if with_refresh:
            self.update()

    def reset_timer(self, with_refresh=True):
        self.disabled = True
        self.seconds = 0
        self.update_value(with_refresh)

    async def update_timer(self):
        while self.running:
            if not self.disabled:
                self.update_value()
                self.seconds += 1
            await asyncio.sleep(1)


class ActionTimerStaticComponent(ActionTimerComponent):
    def update_value(self, with_refresh=True):
        self.value = f'(Всего сегодня: {datetime.timedelta(seconds=self.seconds)})'
        self.update()

    def did_mount(self):
        self.update_value()

class ActivityTrackActionControl(BaseActivityTabActivityTrackControl):
    def __init__(self, state: State, action_relation: ActivityActions):
        super().__init__(state)
        self._action_relation = action_relation
        self._component: ft.Container | None = None
        self._action_timer_total_component: ActionTimerStaticComponent | None = None
        self._action_timer_component: ActionTimerComponent | None = None
        self._start_stop_button: ft.IconButton | None = None
        self._is_started = False

    @property
    def component(self) -> ft.Container:
        return self._component

    @property
    def action_timer_total(self) -> ActionTimerComponent:
        return self.component.content.controls[1]

    @property
    def action_timer(self) -> ActionTimerComponent:
        return self.component.content.controls[3]

    @property
    def action(self) -> Action:
        return self._action_relation.action

    def get_color(self) -> ft.Colors:
        return ft.Colors.GREEN_300 if self._action_relation.is_useful else ft.Colors.RED_300

    def init(self) -> Self:
        color = self.get_color()

        action_tracked_time = self._global_state['activity_track_actions_time'].get(self.action.id, 0)

        self._start_stop_button = ft.IconButton(
            ft.Icons.PLAY_CIRCLE_OUTLINE,
            icon_color=color,
            on_click=self.on_click_start_stop,
        )
        self._action_timer_total_component = ActionTimerStaticComponent(self._action_relation, action_tracked_time)
        self._action_timer_component = ActionTimerComponent(self._action_relation, 0)

        if self._action_relation.is_target:
            font_weight = ft.FontWeight.W_500
        else:
            font_weight = ft.FontWeight.W_400

        self._component = ft.Container(
            padding=10,
            content=ft.Row(
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
        )

        return self

    def on_click_start_stop(self, e):
        if not self._global_state['selected']['activity_track']:
            activity = self._global_state['selected']['activity']
            self._global_state['selected']['activity_track'] = ActivityTrack.create(
                activity=activity
            )

        activity_track = self._global_state['selected']['activity_track']

        to_update_controls = []

        if not self._is_started:
            for action_control_row in self._global_state['controls']['activity']['activity_track']['actions_view'].controls:
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

            action_id = self.action.id
            self._global_state['selected']['action'] = self.action
        else:
            action_id = CONSTS.PAUSE_ACTION_ID
            self.action_timer.disabled = True
            self.action_timer.reset_timer()
            self._component.border = None

            self._start_stop_button.icon = ft.Icons.PLAY_CIRCLE_OUTLINE

            to_update_controls.extend([
                self._component,
                self._start_stop_button,
            ])

        self._global_state['page'].update(*to_update_controls)

        activity_track.change_action(action_id)
        self._is_started = not self._is_started

        ActivityTabHelpers(self._global_state).refresh_activity_actions_total_timers()


class ActivityTrackActionsViewControl(BaseActivityTabActivityTrackControl):
    @property
    def component(self) -> ft.Column:
        return self._state['actions_view']

    def init(self) -> Self:
        self._state['actions_view'] = ft.Column()

        return self
