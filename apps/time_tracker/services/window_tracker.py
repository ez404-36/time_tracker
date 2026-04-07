import asyncio
import datetime

from apps.time_tracker.services.window_control.abstract import WindowData
from apps.time_tracker.services.window_control.base import WindowControl
from core.di import container
from core.store import SessionStore
from core.system_events.event_bus import EventBus
from core.system_events.types import (
    SystemEvent,
    SystemEventChangeActiveWindowsData,
    SystemEventSwitchWindowData,
    SystemEventStartMainTracker,
)

class WindowTracker:
    """
    Отслеживает открытые окна
    """

    def __init__(self):
        self._store: SessionStore = container.session_store
        self._event_bus: EventBus = container.event_bus

        self.running = False
        self.task: asyncio.Task | None = None
        self.current_window: WindowData | None = None
        self.active_windows: list[WindowData] = []

        self.service = WindowControl()

        self._event_bus.subscribe('main_tracker.start', self.on_main_tracker_start)

    def __str__(self) -> str:
        return f'WindowTracker(service={self.service})'

    async def on_main_tracker_start(self, data: SystemEventStartMainTracker):
        if not self.running and data.window_tracking:
            await self.start()

    async def start(self):
        if self.running:
            return

        self._event_bus.publish(
            SystemEvent(
                type='window_tracker.start',
            )
        )

        self.running = True
        self.task = asyncio.create_task(self._run())

    async def stop(self):
        if not self.running:
            return

        self.running = False
        if self.task:
            await self.task

        self._event_bus.publish(
            SystemEvent(
                type='window_tracker.stop',
            )
        )

        self._reset_state()

    async def _run(self):
        while self.running:
            await self._tick()
            await asyncio.sleep(1)

    async def _tick(self):
        now = datetime.datetime.now(datetime.UTC)

        window = self.service.get_active_window()
        if window:
            if not self.current_window:
                self._switch_window(window, now)
            elif window['executable_name'] != self.current_window['executable_name'] or window['window_title'] != self.current_window['window_title']:
                self._switch_window(window, now)

        new_active_windows: list[WindowData] = self.service.get_all_windows()

        if len(new_active_windows) != self.active_windows:
            self.active_windows = new_active_windows
            self._event_bus.publish(
                SystemEvent(
                    type='window_tracker.change_opened_windows',
                    data=SystemEventChangeActiveWindowsData(
                        active_windows=new_active_windows
                    )
                )
            )

    def _switch_window(self, window: WindowData, ts: datetime.datetime):
        self.current_window = window
        self._event_bus.publish(
            SystemEvent(
                type='window_tracker.switch_window',
                data=SystemEventSwitchWindowData(
                    window=window,
                    ts=ts,
                )
            )
        )

    def _reset_state(self):
        self.current_window = None
