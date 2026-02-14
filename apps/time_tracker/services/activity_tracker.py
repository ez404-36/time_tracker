import asyncio
import datetime

from apps.time_tracker.models import IdleSession, WindowSession
from apps.time_tracker.services.window_control.abstract import WindowData
from apps.time_tracker.services.window_control.base import WindowControl
from apps.time_tracker.utils import get_app_name_and_transform_window_title
from core.state import ActivityTabState

# TODO: чисто для тестирования
IDLE_THRESHOLD = 5  # секунд до начала отсчёта бездействия

class ActivityTracker:
    def __init__(self, state: ActivityTabState):
        self._state = state
        self.running = False
        self.is_tracking_enabled = False
        self.task: asyncio.Task | None = None
        self.current_window: WindowData | None = None
        self.window_session: WindowSession | None = None
        self.idle_session: IdleSession | None = None
        self.is_idle = False
        self.service = WindowControl()

    async def start(self):
        if self.running:
            return
        self.running = True
        self.task = asyncio.create_task(self._run())

    async def stop(self):
        if not self.running:
            return

        self.running = False
        if self.task:
            await self.task

        now = datetime.datetime.now(datetime.UTC)
        if self.window_session:
            self.window_session.stop(now)
        if self.idle_session:
            self.idle_session.stop(now)
        self._reset_state()

    async def _run(self):
        while self.running:
            await self._tick()
            await asyncio.sleep(1)

    async def _tick(self):
        now = datetime.datetime.now(datetime.UTC)
        idle_sec = self.service.get_idle_seconds()

        # --- idle state ---
        if idle_sec >= IDLE_THRESHOLD and not self.is_idle:
            self._start_idle(now)
        elif idle_sec < IDLE_THRESHOLD and self.is_idle:
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
        activity_tab = self._state['controls']['activity_tab']
        activity_tab.update_all_active_window_sessions(active_windows)

    def _start_idle(self, ts: datetime.datetime):
        self.is_idle = True
        new_idle_session = IdleSession.create(start_ts=ts)
        self._set_idle_session(new_idle_session)

    def _end_idle(self, ts: datetime.datetime):
        self.is_idle = False
        self.idle_session.stop(ts)
        self._set_idle_session(None)

    def _switch_window(self, window: WindowData, ts: datetime.datetime):
        if self.window_session:
            self.window_session.stop(ts)

        _, title = get_app_name_and_transform_window_title(window['executable_name'], window['window_title'])

        new_window_session = WindowSession.create(
            executable_name=window['executable_name'],
            executable_path=window['executable_path'],
            window_title=title,
            start_ts=ts,
        )

        self.current_window = window

        self._set_window_session(new_window_session)

    def _reset_state(self):
        self.current_window = None
        self._set_window_session(None)
        self._set_idle_session(None)
        self.is_idle = False

    def _set_window_session(self, session: WindowSession | None):
        self.window_session = session
        self._state['selected']['window_session'] = self.window_session
        activity_tab = self._state['controls']['activity_tab']
        activity_tab.update_window_session(session)

    def _set_idle_session(self, session: IdleSession | None):
        self.idle_session = session
        self._state['selected']['idle_session'] = self.idle_session
        activity_tab = self._state['controls']['activity_tab']
        activity_tab.update_idle_session(session)
