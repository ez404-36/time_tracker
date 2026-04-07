import asyncio

import flet as ft

from apps.time_tracker.controls.statistics.index import ActivityStatisticsView
from core.di import container
from core.mixins import SessionStoredComponent
from core.mixins.tracker_info_mixin import TrackerInfoMixin
from core.system_events.types import SystemEventStartMainTracker

from .config_button import TimeTrackingConfigButton
from .current_window import CurrentWindowComponent
from .pause_button import TimeTrackingPauseButton
from .pomodoro_start_rest_button import TimeTrackingPomodoroStartRestButton
from .pomodoro_start_work_button import TimeTrackingPomodoroStartWorkButton
from .resume_button import TimeTrackingResumeButton
from .start_button import TimeTrackingStartButton
from .stop_button import TimeTrackerStopButton
from .time_tracking_status import TimeTrackingStatus


class TimeTrackingComponent(
    ft.Column,
    SessionStoredComponent,
    TrackerInfoMixin,
):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._store = container.session_store
        self._app_settings = container.app_settings
        self._event_bus = container.event_bus

        self._autorefresh_statistics_task: asyncio.Task | None = None

        self._event_bus.subscribe('main_tracker.start', self.on_main_tracker_start)
        self._event_bus.subscribe('main_tracker.stop', self.on_main_tracker_stop)

    @property
    def is_window_tracker_enabled(self) -> bool:
        window_tracker = self._store.get('window_tracker')
        return window_tracker and window_tracker.running

    @property
    def activity_statistics_component(self) -> ActivityStatisticsView:
        return self._store.get('ActivityStatisticsView')

    def build(self):
        buttons_and_status_row = ft.Row(
            controls=[
                TimeTrackingStartButton(),
                TimeTrackingPomodoroStartWorkButton(),
                TimeTrackingPomodoroStartRestButton(),
                TimeTrackingResumeButton(),
                TimeTrackingPauseButton(),
                TimeTrackingStatus(),
                TimeTrackerStopButton(),
                TimeTrackingConfigButton(),
            ]
        )

        self.controls = [
            buttons_and_status_row,
            CurrentWindowComponent(padding=10, visible=False),
        ]

        super().build()

    async def on_main_tracker_start(self, data: SystemEventStartMainTracker):
        self._set_tracker_config_on_start(data)
        if self._tracker_config.window_tracking:
            self.activity_statistics_component.toggle_show_statistics(force_show=True)
            self._autorefresh_statistics_task = asyncio.create_task(self._run_auto_refresh_statistics())

    async def on_main_tracker_stop(self):
        if self._autorefresh_statistics_task:
            await self._autorefresh_statistics_task

    # TODO: большая нагрузка при рефреше статистики: каждую секунду перезапрос в БД и отрисовка.
    #  Пока некритично
    async def _run_auto_refresh_statistics(self):
        while self._is_tracker_running and self._tracker_config.window_tracking:
            self.activity_statistics_component.refresh_statistics()
            await asyncio.sleep(1)
