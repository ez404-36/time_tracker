import datetime

import flet as ft

from apps.time_tracker.consts import ActionIds
from apps.time_tracker.controls.view.active_window import ActiveWindowAndTimerContainer
from apps.time_tracker.controls.view.activity_dropdown import ActivityTabActivityDropdown
from apps.time_tracker.controls.view.edit_activity_button import EditActivityButton
from apps.time_tracker.controls.view.new_activity_button import \
    ActivityTabNewActivityButtonControl
from apps.time_tracker.helpers import TimeTrackDBHelpers
from apps.time_tracker.models import ActivityDayTrack
from core.state import ActivityTabState, State


class ActivityTabViewControl(ft.Container):
    """Таб активности"""

    parent: ft.Tab
    content: ft.Column

    def __init__(self, state: State, **kwargs):
        kwargs.setdefault('padding', 20)
        super().__init__(**kwargs)
        self._state: ActivityTabState = state['tabs']['activity']
        self._activity_selector_control: ActivityTabActivityDropdown | None = None
        self._edit_activity_button_control: EditActivityButton | None = None
        self._new_activity_button_control: ActivityTabNewActivityButtonControl | None = None
        self._action_title: ft.Text | None = None
        self._start_activity_button: ft.IconButton | None = None
        self._pause_activity_button: ft.IconButton | None = None
        self._enable_pomodoro: ft.Checkbox | None = None
        self._activity_track_control: ft.Column | None = None

    def build(self):
        TimeTrackDBHelpers(self._state).refresh_activities()

        self._edit_activity_button_control = EditActivityButton(self._state)
        self._activity_selector_control = ActivityTabActivityDropdown(
            self._state,
            on_change=lambda e: self.on_change_activity_dropdown(e),
        )
        self._state['controls']['view']['activity_selector'] = self._activity_selector_control
        self._new_activity_button_control = ActivityTabNewActivityButtonControl(self._state)
        self._activity_track_control = ft.Column()
        self._action_title = ft.Text(visible=False, size=18, weight=ft.FontWeight.W_500)
        self.build_start_button_and_pomodoro()
        self.build_pause_button()

        target_actions_row = ft.Row(
            [
                self._activity_selector_control,
                self._edit_activity_button_control,
                self._new_activity_button_control,
            ]
        )

        self.content = ft.Column(
            controls=[
                target_actions_row,
                ft.Row(
                    controls=[
                        self._start_activity_button,
                        self._pause_activity_button,
                        self._action_title,
                    ]
                ),
                self._enable_pomodoro,
                self._activity_track_control,
            ]
        )

    def on_change_activity_dropdown(self, e):
        val = int(self._activity_selector_control.value)
        activity = self._state['db']['activities'].get(val)

        if activity == self._state['selected']['activity']:
            return

        self._state['selected']['activity'] = activity
        self._edit_activity_button_control.visible = True
        self._start_activity_button.visible = True
        self._enable_pomodoro.visible = True
        self._enable_pomodoro.value = activity.work_time is not None

        existing_activity_track = ActivityDayTrack.filter(
            activity=activity,
            date=datetime.date.today(),
        ).first()

        self._state['selected']['day_track'] = existing_activity_track

        self._edit_activity_button_control.update()

        self.update()

    def build_start_button_and_pomodoro(self, color: ft.Colors | None = None):
        self._start_activity_button = ft.IconButton(
            ft.Icons.PLAY_CIRCLE_OUTLINE,
            icon_color=color or ft.Colors.GREEN_300,
            on_click=self._on_click_start,
            visible=False,
            icon_size=36,
            tooltip='Начать',
        )
        self._enable_pomodoro = ft.Checkbox(
            label='Включить таймер работы/отдыха',
            visible=False,
        )

    def _on_click_start(self, e):
        self._pause_activity_button.visible = True
        self._start_activity_button.visible = False
        self._enable_pomodoro.visible = False

        activity = self._state['selected']['activity']
        pomodoro_mode = self._enable_pomodoro.value

        if pomodoro_mode:
            seconds = (activity.work_time or 0) * 60
            action_title = 'Работа'
        else:
            seconds = 0
            action_title = 'Отслеживание'

        self._action_title.value = action_title
        self._action_title.visible = True

        self._activity_track_control.controls.append(
            ActiveWindowAndTimerContainer(
                pomodoro_mode=pomodoro_mode,
                seconds=seconds,
            )
        )

        activity_track = TimeTrackDBHelpers(self._state).get_or_create_activity_track()
        activity_track.change_action(ActionIds.START)

        self.parent.update()

    def build_pause_button(self, color: ft.Colors | None = None):
        self._pause_activity_button = ft.IconButton(
            ft.Icons.PAUSE_CIRCLE_OUTLINE,
            icon_color=color or ft.Colors.RED_300,
            on_click=self._on_click_pause,
            icon_size=36,
            visible=False,
            tooltip='Приостановить',
        )

    def _on_click_pause(self, e):
        self._start_activity_button.visible = True
        self._pause_activity_button.visible = False
        self._action_title.visible = False
        self._enable_pomodoro.visible = True

        self._activity_track_control.controls.clear()

        activity_track = self._state['selected']['day_track']
        activity_track.change_action(ActionIds.PAUSE)

        # self.refresh_activity_actions_total_timers()
        self.parent.update()
