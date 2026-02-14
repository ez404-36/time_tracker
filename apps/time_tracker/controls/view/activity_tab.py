import asyncio

import flet as ft

from apps.time_tracker.controls.view.statistics.view import ActivityStatisticsView
from apps.time_tracker.controls.view.timer import TimerComponent
from apps.time_tracker.models import IdleSession, WindowSession
from apps.time_tracker.services.activity_tracker import ActivityTracker
from apps.time_tracker.services.window_control.abstract import WindowData
from apps.time_tracker.utils import get_app_name_and_transform_window_title
from core.state import ActivityTabState, State


class ActivityTabViewControl(ft.Container):
    """Таб активности"""

    parent: ft.Tab
    content: ft.Row

    def __init__(self, state: State, **kwargs):
        kwargs.setdefault('padding', 20)
        super().__init__(**kwargs)
        self._state: ActivityTabState = state['tabs']['activity']

        self._tracking_status: ft.Text | None = None
        self._start_button: ft.IconButton | None = None
        self._stop_button: ft.IconButton | None = None
        self._show_opened_windows: ft.Checkbox | None = None
        self._opened_windows_text: ft.Text | None = None

        self.window_session: ft.Column | None = None
        self.idle_session: ft.Column | None = None
        self.all_window_sessions: ft.Column | None = None
        self._statistics_view: ActivityStatisticsView | None = None

        self._is_activity_tracker_enabled = False
        self._autorefresh_statistics_task: asyncio.Task | None = None

        self.tracker = ActivityTracker(self._state)

    def build(self):
        self.rebuild_tracking_status()
        self._start_button = ft.IconButton(
            icon=ft.Icons.PLAY_CIRCLE_OUTLINE,
            on_click=self._on_click_start,
            tooltip='Включить'
        )
        self._stop_button = ft.IconButton(
            icon=ft.Icons.PAUSE_CIRCLE_OUTLINE,
            visible=False,
            on_click=self._on_click_stop,
            tooltip='Выключить',
        )

        self.build_show_opened_windows_checkbox()
        self._opened_windows_text = ft.Text('Открытые окна', visible=False, size=16, weight=ft.FontWeight.W_400)

        self.all_window_sessions = ft.Column(
            scroll=ft.ScrollMode.ADAPTIVE,
            height=450,
        )

        self.window_session = ft.Column(visible=False)
        self.idle_session = ft.Column(visible=False)

        time_tracking_column = ft.Column(
            width=600,
            controls=[
                ft.Row([
                    self._start_button,
                    self._stop_button,
                    self._tracking_status,
                ]),
                self.window_session,
                self.idle_session,
                ft.Divider(),
                self._show_opened_windows,
                self._opened_windows_text,
                self.all_window_sessions,
            ]
        )

        self._statistics_view = ActivityStatisticsView(self._state)
        self._state['controls']['statistics_view'] = self._statistics_view

        self.content = ft.Row(
            controls=[
                time_tracking_column,
                ft.VerticalDivider(),
                self._statistics_view,
            ]
        )

        self._state['controls']['activity_tab'] = self

    def rebuild_tracking_status(self):
        title = self.get_status_title()
        if not self._tracking_status:
            self._tracking_status = ft.Text(
                value=title,
                size=16,
            )
        else:
            self._tracking_status.value = title

    def get_status_title(self):
        if self._is_activity_tracker_enabled:
            return 'Отслеживание активности...'
        else:
            return 'Отслеживание активности выключено'

    def build_show_opened_windows_checkbox(self):
        self._show_opened_windows = ft.Checkbox(
            label='Показать открытые окна',
            on_change=self.on_click_show_opened_windows,
        )

    def on_click_show_opened_windows(self, e):
        value = e.control.value
        self._opened_windows_text.visible = value
        self.all_window_sessions.visible = value

        self.update()

    async def _on_click_start(self, e):
        self._is_activity_tracker_enabled = True
        await self.tracker.start()
        await self._toggle_affected_on_start_stop()

    async def _on_click_stop(self, e):
        self._is_activity_tracker_enabled = False
        await self.tracker.stop()
        await self._toggle_affected_on_start_stop()

    async def _toggle_affected_on_start_stop(self):
        is_start = self._is_activity_tracker_enabled

        self._start_button.visible = not is_start
        self._stop_button.visible = is_start
        self.rebuild_tracking_status()
        self.window_session.visible = is_start
        self.idle_session.visible = is_start
        self._opened_windows_text.visible = is_start
        self.all_window_sessions.visible = is_start

        if is_start:
            self._statistics_view.toggle_show_statistics(force_show=True)
            self._autorefresh_statistics_task = asyncio.create_task(self._run_auto_refresh_statistics())
        else:
            if self._autorefresh_statistics_task:
                await self._autorefresh_statistics_task

        self.update()

    # TODO: большая нагрузка при рефреше статистики: каждую секунду перезапрос в БД и отрисовка.
    #  Пока некритично
    async def _run_auto_refresh_statistics(self):
        while self._is_activity_tracker_enabled:
            self._statistics_view.refresh_statistics()
            await asyncio.sleep(1)

    def update_idle_session(self, session: IdleSession | None):
        idle_session_control = self.idle_session
        if idle_session_control:
            idle_session_control.controls.clear()
            if session:
                idle_session_control.controls.extend([
                    TimerComponent(),
                    ft.Text(
                        value='Бездействие',
                        color=ft.Colors.RED_300,
                    )
                ])
            idle_session_control.update()

    def update_window_session(self, session: WindowSession | None):
        window_session_control = self.window_session
        if window_session_control and session:
            window_session_control.controls.clear()

            app_title = session.app_name
            if session.window_title:
                app_title += f' ({session.window_title})'

            window_session_control.controls.extend([
                TimerComponent(),
                ft.Text(
                    value=app_title,
                )
            ])
            window_session_control.update()

    def update_all_active_window_sessions(self, active_windows: list[WindowData]):
        all_windows_component = self.all_window_sessions
        all_windows_component.controls.clear()
        for active_window in active_windows:
            app_name, window_title = get_app_name_and_transform_window_title(
                active_window['executable_name'],
                active_window['window_title']
            )
            title = app_name
            if window_title:
                app_name += f' ({window_title})'

            executable_title = active_window['executable_name']
            if active_window['executable_path']:
                executable_title += f' ({active_window['executable_path']}'

            row = ft.Row(
                controls=[
                    ft.Icon(ft.Icons.APPS),
                    ft.Text(
                        value=title,
                        tooltip=executable_title,
                    )
                ]
            )

            all_windows_component.controls.append(row)

        all_windows_component.update()