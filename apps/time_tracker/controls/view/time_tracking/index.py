import asyncio

import flet as ft

from apps.time_tracker.controls.statistics.index import ActivityStatisticsView
from apps.time_tracker.controls.view.pomodoro import PomodoroComponent
from apps.time_tracker.controls.view.time_tracking.current_window import CurrentWindowComponent
from apps.time_tracker.controls.view.total_time import TotalTimerComponent
from apps.time_tracker.models import IdleSession
from apps.time_tracker.services.window_tracker import WindowTracker
from core.di import container
from core.mixins import SessionStoredComponent
from ui.consts import Colors, FontSize, Icons


class TimeTrackingComponent(ft.Column, SessionStoredComponent):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._store = container.session_store
        self._app_settings = container.app_settings
        self._event_bus = container.event_bus

        self._tracking_status: ft.Text | None = None
        self._start_button: ft.IconButton | None = None
        self._stop_button: ft.IconButton | None = None

        self._total_time_component: TotalTimerComponent | None = None
        self._pomodoro_component: PomodoroComponent | None = None

        self._main_row: ft.Row | None = None

        self.window_session_component: CurrentWindowComponent | None = None
        self.idle_session_ctrl: ft.Column | None = None

        self._idle_session: IdleSession | None = None

        self._autorefresh_statistics_task: asyncio.Task | None = None

    @property
    def is_window_tracker_enabled(self) -> bool:
        return self._store.get('is_window_tracker_enabled')

    @property
    def tracker(self) -> WindowTracker:
        return self._store.get('window_tracker')

    @property
    def activity_statistics_component(self) -> ActivityStatisticsView:
        return self._store.get('ActivityStatisticsView')

    def build(self):
        self._start_button = ft.IconButton(
            icon=ft.Icon(
                icon=Icons.START,
                color=Colors.GREEN_LIGHT,
            ),
            on_click=self._on_click_start,
            tooltip='Включить'
        )
        self._stop_button = ft.IconButton(
            icon=ft.Icon(
                icon=Icons.STOP,
                color=Colors.RED_LIGHT,
            ),
            visible=False,
            on_click=self._on_click_stop,
            tooltip='Выключить',
        )
        self.rebuild_tracking_status_text()
        self.window_session_component = CurrentWindowComponent(visible=False)
        self.idle_session_ctrl = ft.Column(visible=False)
        self._total_time_component = TotalTimerComponent(visible=False)
        self._pomodoro_component = PomodoroComponent(visible=self._app_settings.enable_pomodoro)

        self._main_row = ft.Row(
            controls=[
                self._start_button,
                self._stop_button,
                self._tracking_status,
                self._total_time_component,
            ]
        )

        self.controls = [
            self._main_row,
            self._pomodoro_component,
            self.window_session_component,
            self.idle_session_ctrl,
        ]

        super().build()

    async def start_total_timer(self):
        self._delete_total_time_component()
        self._main_row.controls.append(self._total_time_component)
        self.update()

    async def stop_total_timer(self):
        self._delete_total_time_component()
        self.update()

    def _delete_total_time_component(self):
        if self._total_time_component and self._total_time_component in self._main_row.controls:
            self._main_row.controls.remove(self._total_time_component)

        self._total_time_component = TotalTimerComponent()

    def rebuild_tracking_status_text(self):
        title = self.get_status_title()
        if not self._tracking_status:
            self._tracking_status = ft.Text(
                value=title,
                size=FontSize.H5,
            )
        else:
            self._tracking_status.value = title

    def get_status_title(self):
        if self.is_window_tracker_enabled:
            return 'Отслеживание активности...'
        else:
            return 'Отслеживание активности выключено'

    async def _on_click_start(self, e):
        self._store.set('is_window_tracker_enabled', True)
        await self.tracker.start()
        self._autorefresh_statistics_task = asyncio.create_task(self._run_auto_refresh_statistics())
        await self.start_total_timer()
        await self._update_components_visibility_on_start_stop()

    async def _on_click_stop(self, e):
        await self.tracker.stop()

        await self.stop_total_timer()

        if self._autorefresh_statistics_task:
            await self._autorefresh_statistics_task

        await self._update_components_visibility_on_start_stop()

    async def _update_components_visibility_on_start_stop(self):
        is_start = self.is_window_tracker_enabled

        self._start_button.visible = not is_start
        self._stop_button.visible = is_start
        self.rebuild_tracking_status_text()
        self.window_session_component.visible = is_start
        self.idle_session_ctrl.visible = is_start

        if is_start:
            self.activity_statistics_component.toggle_show_statistics(force_show=True)

            await self.start_total_timer()
        else:
            await self.stop_total_timer()

        self.update()

    # TODO: большая нагрузка при рефреше статистики: каждую секунду перезапрос в БД и отрисовка.
    #  Пока некритично
    async def _run_auto_refresh_statistics(self):
        while self.is_window_tracker_enabled:
            self.activity_statistics_component.refresh_statistics()
            await asyncio.sleep(1)
