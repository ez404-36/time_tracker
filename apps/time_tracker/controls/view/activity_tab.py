import asyncio

import flet as ft

from apps.time_tracker.controls.view.statistics.view import ActivityStatisticsView
from apps.time_tracker.services.activity_tracker import ActivityTracker
from core.state import ActivityTabState, State


class ActivityTabViewControl(ft.Container):
    """Таб активности"""

    parent: ft.Tab
    content: ft.Row

    def __init__(self, state: State, **kwargs):
        kwargs.setdefault('padding', 20)
        super().__init__(**kwargs)
        self._state: ActivityTabState = state['tabs']['activity']

        self._status: ft.Text | None = None
        self._start_button: ft.IconButton | None = None
        self._stop_button: ft.IconButton | None = None
        self._opened_windows_text: ft.Text | None = None

        self.window_session: ft.Column | None = None
        self.idle_session: ft.Column | None = None
        self.all_window_sessions: ft.Column | None = None
        self._statistics_view: ActivityStatisticsView | None = None

        self._is_activity_tracker_enabled = False
        self._autorefresh_statistics_task: asyncio.Task | None = None

        self.tracker = ActivityTracker(self._state)

    def build(self):
        self._status = ft.Text(
            value='Отслеживание активности выключено',
            size=16,
        )
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
        self._opened_windows_text = ft.Text('Открытые окна', visible=False)

        self.all_window_sessions = ft.Column()
        self._state['controls']['all_window_sessions'] = self.all_window_sessions

        self.window_session = ft.Column(visible=False)
        self._state['controls']['window_session'] = self.window_session

        self.idle_session = ft.Column(visible=False)
        self._state['controls']['idle_session'] = self.idle_session

        time_tracking_column = ft.Column(
            width=600,
            controls=[
                ft.Row([
                    self._start_button,
                    self._stop_button,
                    self._status,
                ]),
                self.window_session,
                self.idle_session,
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
        self._status.value = 'Отслеживание активности...' if is_start else 'Отслеживание активности выключено'
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

    async def _run_auto_refresh_statistics(self):
        while self._is_activity_tracker_enabled:
            await asyncio.sleep(5)  # рефреш статистики каждые 5 секунд
            self._statistics_view.refresh_statistics()
