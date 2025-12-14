from typing import Self

import flet as ft
from flet.core.border import Border, BorderSide

from apps.time_tracker.consts import PAUSE_ACTION_ID
from apps.time_tracker.controls.view.action_timer import ActionTimerComponent, \
    ActionTimerStaticComponent
from apps.time_tracker.helpers import TimeTrackDBHelpers
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
        self._start_button: ft.IconButton | None = None
        self._pause_button: ft.IconButton | None = None
        self._is_started = False

    @property
    def neighbours(self) -> list[Self]:
        return self.parent.controls

    def get_controls(self) -> list[ft.Control]:
        content: ft.Row = self.content
        return content.controls

    @property
    def action_timer_total(self) -> ActionTimerComponent:
        return self._action_timer_total_component

    @property
    def action_timer(self) -> ActionTimerComponent:
        return self._action_timer_component

    @property
    def action(self) -> Action:
        return self._action

    def get_color(self) -> ft.Colors:
        return ft.Colors.GREEN_300 if self._action.is_useful else ft.Colors.RED_300

    def build(self) -> Self:
        color = self.get_color()

        action_tracked_time = TimeTrackDBHelpers(self._state).get_activity_actions_tracked_time().get(self.action.id, 0)
        self.build_start_button(color)
        self.build_pause_button(color)

        self._action_timer_total_component = ActionTimerStaticComponent(action_tracked_time)

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
                self._start_button,
                self._pause_button,
            ],
        )

    def build_start_button(self, color: ft.Colors):
        self._start_button = ft.IconButton(
            ft.Icons.PLAY_CIRCLE_OUTLINE,
            icon_color=color,
            on_click=self._on_click_start,
        )

    def build_pause_button(self, color: ft.Colors):
        self._pause_button = ft.IconButton(
            ft.Icons.PAUSE_CIRCLE_OUTLINE,
            icon_color=color,
            on_click=self._on_click_pause,
            visible=False,
        )

    def _on_click_pause(self, e):
        self.update_controls_on_inactive()

        activity_track = self._state['selected']['activity_track']
        activity_track.change_action(PAUSE_ACTION_ID)

        self.refresh_activity_actions_total_timers()
        self.parent.update()

    def update_controls_on_inactive(self):
        """Изменить состояние компонентов для неактивного действия"""
        self._pause_button.visible = False
        self._start_button.visible = True
        self.border = None
        self.remove_action_timer()

    def _on_click_start(self, e):
        self._pause_button.visible = True
        self._start_button.visible = False

        self.set_border()

        activity_track = self._get_or_create_activity_track()
        prev_action = self._state['selected']['action']

        for action_control_container in self.neighbours:
            if action_control_container == self:
                continue

            row_action: Action = action_control_container.action

            if prev_action == row_action:
                action_control_container.update_controls_on_inactive()

        self._state['selected']['action'] = self._action
        self.add_action_timer()

        activity_track.change_action(self._action.id)

        self.refresh_activity_actions_total_timers()
        self.parent.update()

    def set_border(self):
        color = self.get_color()
        bs = BorderSide(2, color)
        border = Border(left=bs, top=bs, right=bs, bottom=bs)
        self.border = border

    def refresh_activity_actions_total_timers(self):
        tracked_time = TimeTrackDBHelpers(self._state).get_activity_actions_tracked_time()
        for action_control_content in self.neighbours: # type: Self
            action = action_control_content.action
            action_tracked_time = tracked_time.get(action.id, 0)

            total_timer_control = action_control_content._action_timer_total_component
            total_timer_control.seconds = action_tracked_time
            total_timer_control.update_value(with_refresh=False)

    def remove_action_timer(self):
        if self._action_timer_component is not None:
            self.get_controls().remove(self._action_timer_component)
            self._action_timer_component = None

    def add_action_timer(self):
        self._action_timer_component = ActionTimerComponent()
        self.get_controls().append(self._action_timer_component)

    def _get_or_create_activity_track(self) -> ActivityTrack:
        if not self._state['selected']['activity_track']:
            activity = self._state['selected']['activity']
            self._state['selected']['activity_track'] = ActivityTrack.create(
                activity=activity
            )
        return self._state['selected']['activity_track']
