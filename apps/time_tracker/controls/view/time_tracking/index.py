import asyncio

import flet as ft

from apps.time_tracker.controls.statistics.index import ActivityStatisticsView
from apps.time_tracker.controls.view.time_tracking.current_window import CurrentWindowComponent
from apps.time_tracker.controls.view.time_tracking_status import TimeTrackingStatus
from apps.time_tracker.models import IdleSession
from apps.time_tracker.services.window_tracker import WindowTracker
from core.di import container
from core.mixins import SessionStoredComponent
from core.system_events.types import SystemEventStartMainTracker
from ui.consts import Colors, Icons


class TimeTrackingComponent(ft.Column, SessionStoredComponent):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._store = container.session_store
        self._app_settings = container.app_settings
        self._event_bus = container.event_bus

        self._tracking_status: TimeTrackingStatus | None = None
        self._start_button: ft.IconButton | None = None
        self._stop_button: ft.IconButton | None = None
        self._tracking_config_button: ft.IconButton | None = None

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
        self._tracking_config_button = ft.IconButton(
            icon=ft.Icon(
                icon=Icons.SETTINGS,
                color=Colors.BLUE_LIGHT,
            ),
            visible=True,
            # on_click=lambda e: self.page.show_dialog(),
            tooltip='Параметры контроля активности',
        )
        self._tracking_status = TimeTrackingStatus()
        self.window_session_component = CurrentWindowComponent(visible=False)
        self.idle_session_ctrl = ft.Column(visible=False)

        self._main_row = ft.Row(
            controls=[
                self._start_button,
                self._stop_button,
                self._tracking_status,
                self._tracking_config_button,
            ]
        )

        self.controls = [
            self._main_row,
            self.window_session_component,
            self.idle_session_ctrl,
        ]

        super().build()

    async def _on_click_start(self, e):
        self._event_bus.publish(
            'main_tracker.start',
            SystemEventStartMainTracker(
                idle_tracking=self._app_settings.enable_idle_tracking,
                window_tracking=self._app_settings.enable_window_tracking,
                pomodoro_tracking=self._app_settings.enable_pomodoro,
            )
        )
        self._store.set('is_window_tracker_enabled', True)
        await self.tracker.start()
        self._autorefresh_statistics_task = asyncio.create_task(self._run_auto_refresh_statistics())
        await self._update_components_visibility_on_start_stop()

    async def _on_click_stop(self, e):
        await self.tracker.stop()

        if self._autorefresh_statistics_task:
            await self._autorefresh_statistics_task

        await self._update_components_visibility_on_start_stop()

    async def _update_components_visibility_on_start_stop(self):
        is_start = self.is_window_tracker_enabled

        self._start_button.visible = not is_start
        self._stop_button.visible = is_start
        self.window_session_component.visible = is_start
        self.idle_session_ctrl.visible = is_start

        if is_start:
            self.activity_statistics_component.toggle_show_statistics(force_show=True)

        self.update()

    # TODO: большая нагрузка при рефреше статистики: каждую секунду перезапрос в БД и отрисовка.
    #  Пока некритично
    async def _run_auto_refresh_statistics(self):
        while self.is_window_tracker_enabled:
            self.activity_statistics_component.refresh_statistics()
            await asyncio.sleep(1)
