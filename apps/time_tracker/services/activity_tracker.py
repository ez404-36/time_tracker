import asyncio
import datetime

from apps.app_settings.models import AppSettings
from apps.time_tracker.services.window_control import WindowControl
from core.di import container
from core.system_events.event_bus import EventBus
from core.system_events.types import SystemEvent, SystemEventTimestampData


class ActivityTracker:
    """
    Занимается отслеживанием активности/бездействия пользователя
    """

    def __init__(self):
        self.running = False
        self.is_idle = False

        self._event_bus: EventBus = container.event_bus
        self._app_settings: AppSettings = container.app_settings

        self._idle_threshold: int | None = None
        self._task: asyncio.Task | None = None

        self._service = WindowControl()

    async def start(self):
        if self.running:
            return

        self._idle_threshold = self._app_settings.idle_threshold
        self.running = True
        self._task = asyncio.create_task(self._run())

        self._event_bus.publish(
            SystemEvent(
                type='activity_tracker.start',
            )
        )

    async def stop(self):
        if not self.running:
            return

        self.running = False
        if self._task:
            await self._task

        self._reset_state()

        self._event_bus.publish(
            SystemEvent(
                type='activity_tracker.stop',
            )
        )

    async def _run(self):
        while self.running:
            await self._tick()
            await asyncio.sleep(1)

    async def _tick(self):
        now = datetime.datetime.now(datetime.UTC)

        idle_sec = self._service.get_idle_seconds()

        if idle_sec >= self._idle_threshold and not self.is_idle:
            self._on_detect_idle(now)
        elif idle_sec < self._idle_threshold and self.is_idle:
            self._end_idle(now)

    def _on_detect_idle(self, ts: datetime.datetime):
        self.is_idle = True
        self._event_bus.publish(
            SystemEvent(
                type='activity_tracker.detect_idle',
                data=SystemEventTimestampData(
                    ts=ts,
                )
            )
        )

    def _end_idle(self, ts: datetime.datetime):
        self.is_idle = False
        self._event_bus.publish(
            SystemEvent(
                type='activity_tracker.stop_idle',
                data=SystemEventTimestampData(
                    ts=ts,
                )
            )
        )

    def _reset_state(self):
        self.is_idle = False
