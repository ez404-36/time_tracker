import flet as ft

from apps.time_tracker.services.activity_tracker import ActivityTracker
from core.state import ActivityTabState, State


class ActivityTabViewControl(ft.Container):
    """Таб активности"""

    parent: ft.Tab
    content: ft.Column

    def __init__(self, state: State, **kwargs):
        kwargs.setdefault('padding', 20)
        super().__init__(**kwargs)
        self._state: ActivityTabState = state['tabs']['activity']

        self._status: ft.Text | None = None
        self._start_button: ft.IconButton | None = None
        self._stop_button: ft.IconButton | None = None

        self._all_window_sessions: ft.Column | None = None

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

        self._all_window_sessions = ft.Column()
        self._state['controls']['all_window_sessions'] = self._all_window_sessions

        self.content = ft.Column(
            controls=[
                ft.Row([
                    self._start_button,
                    self._stop_button,
                    self._status,
                ]),
                self._all_window_sessions,
            ]
        )

    async def _on_click_start(self, e):
        await self.tracker.start()
        self._start_button.visible = False
        self._stop_button.visible = True
        self._status.value = 'Отслеживание активности...'
        self.update()

    async def _on_click_stop(self, e):
        await self.tracker.stop()
        self._start_button.visible = True
        self._stop_button.visible = False
        self._status.value = 'Отслеживание активности выключено'
        self.update()
