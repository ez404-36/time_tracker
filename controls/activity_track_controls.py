import asyncio
import datetime
from typing import Self

import flet as ft

from controls.base_control import BaseControl
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
        self.value = datetime.timedelta(seconds=self.seconds)
        self.update()

    def will_unmount(self):
        self.running = False

    async def update_timer(self):
        while self.running:
            if not self.disabled:
                self.value = datetime.timedelta(seconds=self.seconds)
                self.update()
                self.seconds += 1
            await asyncio.sleep(1)


class ActivityTrackActionControl(BaseActivityTabActivityTrackControl):
    def __init__(self, state: State, action_relation: ActivityActions):
        super().__init__(state)
        self._action_relation = action_relation
        self._component: ft.Container | None = None
        self._action_timer_component: ActionTimerComponent | None = None
        self._start_stop_button: ft.IconButton | None = None
        self._is_started = False

    @property
    def component(self) -> ft.Container:
        return self._component

    @property
    def action(self) -> Action:
        return self._action_relation.action

    def init(self) -> Self:
        color = ft.Colors.GREEN_300 if self._action_relation.is_target else ft.Colors.RED_300

        action_tracked_time = self._global_state['activity_track_actions_time'].get(self.action.id, 0)

        self._start_stop_button = ft.IconButton(
            ft.Icons.PLAY_CIRCLE_OUTLINE,
            icon_color=color,
            on_click=self.on_click_start_stop,
        )
        self._action_timer_component = ActionTimerComponent(self._action_relation, action_tracked_time)

        # TODO: при старте одного действия стопать другое действие
        # TODO: при стопе действия обновлять стейт и данные в БД, удалять таймер и выводить общее время

        self._component = ft.Container(
            padding=10,
            content=ft.Row(
                controls=[
                    ft.Text(
                        self.action.title,
                        size=14,
                        weight=ft.FontWeight.W_400,
                        color=color,
                        width=120,
                    ),
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

        if not self._is_started:
            self._start_stop_button.icon = ft.Icons.PAUSE_CIRCLE_OUTLINE
        else:
            self._start_stop_button.icon = ft.Icons.PLAY_CIRCLE_OUTLINE

        self._start_stop_button.update()

        if not self._is_started:
            for action_control_row in self._global_state['controls']['activity']['activity_track']['actions_view'].controls:
                timer_control = action_control_row.content.controls[-1]
                timer_control.disabled = not timer_control == self._action_timer_component
                timer_control.update()
            action_id = self.action.id
        else:
            action_id = CONSTS.PAUSE_ACTION_ID

        activity_track.change_action(action_id)
        self._is_started = not self._is_started


        # self._state['active_action_timer'] = self._action_timer_component
        # self._action_timer_component.active = True
        # activity_track.change_action(self.action.id)


class ActivityTrackActionsViewControl(BaseActivityTabActivityTrackControl):
    @property
    def component(self) -> ft.Column:
        return self._state['actions_view']

    def init(self) -> Self:
        self._state['actions_view'] = ft.Column()

        return self
