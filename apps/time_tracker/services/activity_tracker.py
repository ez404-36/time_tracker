import asyncio
import datetime

from apps.app_settings.models import AppSettings
from apps.events.models import Event
from apps.events.consts import EventActor, EventType
from apps.time_tracker.services.window_control.abstract import WindowData
from apps.time_tracker.services.window_control.base import WindowControl
from core.di import container
from core.store import SessionStore


class ActivityTracker:
    def __init__(self):
        self._store: SessionStore = container.session_store
        self._app_settings: AppSettings = container.app_settings

        self.running = False
        self.idle_threshold: int | None = None
        self.task: asyncio.Task | None = None
        self.current_window: WindowData | None = None
        self.is_idle = False
        self.service = WindowControl()

    @property
    def time_tracking_component(self):
        return self._store.get('TimeTrackingComponent')

    @property
    def opened_windows_component(self):
        return self._store.get('OpenedWindowsComponent')

    async def start(self):
        if self.running:
            return
        self.idle_threshold = self._app_settings.idle_threshold
        self.running = True
        self.task = asyncio.create_task(self._run())

    async def stop(self):
        if not self.running:
            return

        self.running = False
        if self.task:
            await self.task

        await self.time_tracking_component.stop_tracking()

        self._reset_state()

    async def _run(self):
        while self.running:
            await self._tick()
            await asyncio.sleep(1)

    async def _tick(self):
        now = datetime.datetime.now(datetime.UTC)

        idle_sec = self.service.get_idle_seconds()

        # --- idle state ---
        if idle_sec >= self.idle_threshold and not self.is_idle:
            self._start_idle(now)
        elif idle_sec < self.idle_threshold and self.is_idle:
            self._end_idle(now)

        # --- active window ---
        if not self.is_idle:
            window = self.service.get_active_window()
            if window:
                if not self.current_window:
                    self._switch_window(window, now)
                elif window['executable_name'] != self.current_window['executable_name'] or window['window_title'] != self.current_window['window_title']:
                    self._switch_window(window, now)

        active_windows = self.service.get_all_windows()
        self.opened_windows_component.update_all_active_window_sessions(active_windows)

    def _start_idle(self, ts: datetime.datetime):
        self.is_idle = True
        Event.create(
            type=EventType.DETECT_IDLE,
            actor=EventActor.SYSTEM,
            ts=ts,
        )
        self.time_tracking_component.create_idle_session(ts)

    def _end_idle(self, ts: datetime.datetime):
        self.is_idle = False
        Event.create(
            type=EventType.END_IDLE,
            actor=EventActor.SYSTEM,
            ts=ts,
        )
        self.time_tracking_component.stop_idle_session(ts)

    def _switch_window(self, window: WindowData, ts: datetime.datetime):
        self.current_window = window

        Event.create(
            type=EventType.SWITCH_WINDOW,
            actor=EventActor.USER,
            data=window,
            ts=ts,
        )

        self.time_tracking_component.switch_window_session(window, ts)

    def _reset_state(self):
        self.current_window = None
        self.is_idle = False
