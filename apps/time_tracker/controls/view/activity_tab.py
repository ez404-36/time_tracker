import asyncio
import datetime

import flet as ft

from apps.time_tracker.controls.view.statistics.view import ActivityStatisticsView
from apps.time_tracker.controls.view.timer import TimerComponent
from apps.time_tracker.models import IdleSession, WindowSession
from apps.time_tracker.services.activity_tracker import ActivityTracker
from apps.time_tracker.services.window_control.abstract import WindowData
from apps.time_tracker.utils import get_app_name_and_transform_window_title
from core.settings import app_settings
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

        self.window_session_ctrl: ft.Column | None = None
        self.idle_session_ctrl: ft.Column | None = None
        self.all_window_sessions: ft.Column | None = None
        self._statistics_view: ActivityStatisticsView | None = None

        self._window_session: WindowSession | None = None
        self._idle_session: IdleSession | None = None
        self._is_activity_tracker_enabled = False
        self._is_active_windows_showed = False
        self._autorefresh_statistics_task: asyncio.Task | None = None
        self._current_window_data: WindowData | None = None  # данные текущего окна, полученные из трекера

        self._app_settings = app_settings
        self.tracker = ActivityTracker(self._state)

    def build(self):
        self.rebuild_tracking_status_text()
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
            height=350,
        )

        self.window_session_ctrl = ft.Column(visible=False)
        self.idle_session_ctrl = ft.Column(visible=False)

        time_tracking_column = ft.Column(
            width=600,
            controls=[
                ft.Row([
                    self._start_button,
                    self._stop_button,
                    self._tracking_status,
                ]),
                self.window_session_ctrl,
                self.idle_session_ctrl,
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

    def rebuild_tracking_status_text(self):
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

    async def on_click_show_opened_windows(self, e):
        value = e.control.value
        self._is_active_windows_showed = value

        self._opened_windows_text.visible = value
        self.all_window_sessions.visible = value

        if not self._is_activity_tracker_enabled:
            # Если отслеживание активности не включено, включим трекер вручную
            if value:
                await self.tracker.start()
            else:
                await self.tracker.stop()

        self.update()

    async def _on_click_start(self, e):
        self._is_activity_tracker_enabled = True
        if self._is_active_windows_showed:
            if self._current_window_data:
                self.switch_window_session(self._current_window_data, datetime.datetime.now(datetime.UTC))
        else:
            await self.tracker.start()

        await self._toggle_affected_on_start_stop()

    async def _on_click_stop(self, e):
        if self._is_active_windows_showed:
            await self.stop_tracking(datetime.datetime.now(datetime.UTC))
        else:
            await self.tracker.stop()

    async def _toggle_affected_on_start_stop(self):
        is_start = self._is_activity_tracker_enabled

        self._start_button.visible = not is_start
        self._stop_button.visible = is_start
        self.rebuild_tracking_status_text()
        self.window_session_ctrl.visible = is_start
        self.idle_session_ctrl.visible = is_start

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

    def create_idle_session(self, ts: datetime.datetime):
        if not self._is_activity_tracker_enabled:
            return

        self._idle_session = IdleSession.create(start_ts=ts)
        self._app_settings.play_idle_start_sound()

        idle_session_control = self.idle_session_ctrl
        idle_session_control.controls.clear()
        if self._idle_session:
            idle_session_control.controls.extend([
                TimerComponent(),
                ft.Text(
                    value='Бездействие',
                    color=ft.Colors.RED_300,
                )
            ])
        idle_session_control.update()

    def switch_window_session(self, window: WindowData, ts: datetime.datetime):
        self._current_window_data = window
        if not self._is_activity_tracker_enabled:
            return

        _, title = get_app_name_and_transform_window_title(window['executable_name'], window['window_title'])

        if self._window_session:
            self._window_session.stop(ts)

        self._window_session = WindowSession.create(
            executable_name=window['executable_name'],
            executable_path=window['executable_path'],
            window_title=title,
            start_ts=ts,
        )

        window_session_control = self.window_session_ctrl

        window_session_control.controls.clear()

        app_title = self._window_session.app_name
        if self._window_session.window_title:
            app_title += f' ({self._window_session.window_title})'

        window_session_control.controls.extend([
            TimerComponent(),
            ft.Text(
                value=app_title,
            )
        ])
        window_session_control.update()

    def stop_idle_session(self, ts: datetime.datetime):
        if not self._is_activity_tracker_enabled:
            return

        if self._idle_session:
            self._idle_session.stop(ts)

        self._idle_session = None
        self.idle_session_ctrl.controls.clear()
        self.idle_session_ctrl.update()

    async def stop_tracking(self, ts: datetime.datetime):
        self.stop_window_session(ts)
        self.stop_idle_session(ts)
        self._is_activity_tracker_enabled = False
        await self._toggle_affected_on_start_stop()

    def stop_window_session(self, ts: datetime.datetime):
        if not self._is_activity_tracker_enabled:
            return

        if self._window_session:
            self._window_session.stop(ts)

        self._window_session = None
        self.window_session_ctrl.controls.clear()
        self.window_session_ctrl.update()

    def update_all_active_window_sessions(self, active_windows: list[WindowData]):
        if not self._is_active_windows_showed:
            return

        self._opened_windows_text.value = f'Открытые окна ({len(active_windows)})'
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
                        tooltip=ft.Tooltip(
                            message=executable_title,
                            # TODO: тултип мигает
                        ),
                    )
                ]
            )

            all_windows_component.controls.append(row)

        self.update()
