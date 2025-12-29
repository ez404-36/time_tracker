import asyncio
import datetime

import flet as ft

from apps.time_tracker.controls.view.timer import TimerComponent
from apps.time_tracker.models import IdleSession, WindowSession
from apps.time_tracker.services.window_control.abstract import WindowData
from apps.time_tracker.services.window_control.base import WindowControl
from core.state import ActivityTabState

IDLE_THRESHOLD = 60  # секунд до начала отсчёта бездействия

class ActivityTracker:
    def __init__(self, state: ActivityTabState):
        self._state = state
        self.running = False
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
                elif window['app_name'] != self.current_window['app_name'] or window['title'] != self.current_window['title']:
                    self._switch_window(window, now)

        all_windows_component = self._state['controls']['all_window_sessions']
        if all_windows_component:
            active_windows = self.service.get_all_windows()
            all_windows_component.controls.clear()
            for active_window in active_windows:
                title = f'{active_window["app_name"]} ({active_window["title"]})'

                row = ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.APPS),
                        ft.Text(
                            value=title,
                        )
                    ]
                )

                all_windows_component.controls.append(row)

            all_windows_component.update()

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

        new_window_session = WindowSession.create(
            app_name=window['app_name'],
            window_title=window['title'],
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
        window_session_control = self._state['controls']['window_session']
        if window_session_control:
            window_session_control.controls.clear()
            window_session_control.controls.extend([
                TimerComponent(),
                ft.Text(
                    value=f'{session.app_name} ({session.window_title})'
                )
            ])
            window_session_control.update()

    def _set_idle_session(self, session: IdleSession | None):
        self.idle_session = session
        self._state['selected']['idle_session'] = self.idle_session
        idle_session = self._state['controls']['idle_session']
        if idle_session:
            idle_session.controls.clear()
            idle_session.controls.extend([
                TimerComponent(),
                ft.Text(
                    value=f'Бездействие',
                    color=ft.Colors.RED_300,
                )
            ])
            idle_session.update()
