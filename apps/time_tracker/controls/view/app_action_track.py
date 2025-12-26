from typing import Self

import flet as ft
import pywinctl
from flet.core.border import Border, BorderSide

from apps.time_tracker.controls.view.timer import TimerComponent, TimerStaticComponent
from apps.time_tracker.helpers import TimeTrackDBHelpers
from apps.time_tracker.services.window_control import WindowControl
from core.state import ActivityTabState


class AppActionTrackContainer(ft.Container):
    """
    Компонент статистики определенного действия за день. Отображает:
    - действие (PID процесса, название вкладки, время)
    """

    def __init__(self, state: ActivityTabState, window: pywinctl.Window, **kwargs):
        kwargs.setdefault('padding', 10)
        super().__init__(**kwargs)
        self._state = state
        self._window = window
        self._app_path = WindowControl().get_executable_path(window)

        self._action_timer_total_component: TimerStaticComponent | None = None
        self._is_started = False

    @property
    def neighbours(self) -> list[Self]:
        return self.parent.controls

    def get_controls(self) -> list[ft.Control]:
        content: ft.Row = self.content
        return content.controls

    @property
    def action_timer_total(self) -> TimerComponent:
        return self._action_timer_total_component

    @property
    def title(self):
        return f'{self._window.getAppName()}: {self._window.title}'

    def get_color(self) -> ft.Colors:
        return ft.Colors.GREEN_300# if self._action.is_useful else ft.Colors.RED_300

    def build(self):
        color = self.get_color()

        action_tracked_time = (
            TimeTrackDBHelpers(self._state)
            .get_activity_actions_tracked_time()
            .get(self._app_path, 0)
        )

        self._action_timer_total_component = TimerStaticComponent(action_tracked_time)

        # if self._action.is_target:
        #     font_weight = ft.FontWeight.W_500
        # else:
        font_weight = ft.FontWeight.W_400

        self.content = ft.Row(
            controls=[
                ft.Text(
                    self.title,
                    size=14,
                    weight=font_weight,
                    color=color,
                    width=120,
                ),
                self._action_timer_total_component,
            ],
        )

    def set_border(self):
        color = self.get_color()
        bs = BorderSide(2, color)
        border = Border(left=bs, top=bs, right=bs, bottom=bs)
        self.border = border

    def refresh_activity_actions_total_timers(self):
        tracked_time = TimeTrackDBHelpers(self._state).get_activity_actions_tracked_time()
        for action_control_content in self.neighbours: # type: Self
            app_path = action_control_content._app_path
            action_tracked_time = tracked_time.get(app_path, 0)

            total_timer_control = action_control_content._action_timer_total_component
            total_timer_control.seconds = action_tracked_time
            total_timer_control.update_value(with_refresh=False)
