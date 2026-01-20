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

        current_state_column = ft.Column(
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

        self.content = ft.Row(
            controls=[
                current_state_column,
                ft.VerticalDivider(),
                # self._statistics_view,
            ]
        )

    def _on_change_stat_drp(self, e):
        print('Changed', e)

    async def _on_click_start(self, e):
        await self.tracker.start()
        self._toggle_affected_on_start_stop(True)

    async def _on_click_stop(self, e):
        await self.tracker.stop()
        self._toggle_affected_on_start_stop(False)

    def _toggle_affected_on_start_stop(self, is_start: bool):
        self._start_button.visible = not is_start
        self._stop_button.visible = is_start
        self._status.value = 'Отслеживание активности...' if is_start else 'Отслеживание активности выключено'
        self.window_session.visible = is_start
        self.idle_session.visible = is_start
        self._opened_windows_text.visible = is_start
        self.all_window_sessions.visible = is_start
        self.update()
