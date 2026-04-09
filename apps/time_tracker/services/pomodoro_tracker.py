__all__ = (
    'PomodoroTracker',
)

from typing import TYPE_CHECKING

from apps.time_tracker.types import PomodoroTimerStatus
from core.system_events import types as system_event_types

if TYPE_CHECKING:
    from apps.app_settings.models import AppSettings
    from core.system_events.event_bus import EventBus


pomodoro_status_to_next_status_map: dict[PomodoroTimerStatus, list[PomodoroTimerStatus]] = {
    'disabled': ['working'],
    'working': ['working_pause', 'working_stop'],
    'working_pause': ['working'],
    'working_stop': ['resting'],
    'resting': ['resting_pause', 'resting_stop'],
    'resting_pause': ['resting'],
    'resting_stop': ['working'],
}


class PomodoroTracker:
    """
    Сервис по взаимодействию с таймером Помодоро.
    Принцип работы: поочередный запуск таймеров работы/отдыха
    """

    def __init__(self, event_bus: 'EventBus', app_settings: 'AppSettings'):
        self._event_bus = event_bus
        self._app_settings = app_settings

        self._status: PomodoroTimerStatus = 'disabled'

        self._event_bus.subscribe('main_tracker.start', self.start)
        self._event_bus.subscribe('main_tracker.pause', self.pause)
        self._event_bus.subscribe('main_tracker.resume', self.resume)
        self._event_bus.subscribe('main_tracker.stop', self.stop)

    def __str__(self):
        return f'PomodoroTracker(status={self.status})'

    @property
    def status(self) -> PomodoroTimerStatus:
        return self._status

    @property
    def is_on_pause(self) -> bool:
        return self._status in ['working_pause', 'resting_pause']

    def start(self, data: system_event_types.SystemEventStartMainTracker) -> None:
        """Первичный запуск работы по таймеру Помодоро"""

        if data.pomodoro_tracking:
            self._change_status('working')

    def stop_current_timer(self):
        """Остановка текущего таймера"""

        if self._status == 'working':
            self._change_status('working_stop')
        elif self._status == 'resting':
            self._change_status('resting_stop')
        else:
            self._create_error_change_status_event(self._status, 'unknown')

    def start_next_timer(self):
        """Запуск следующего таймера"""

        if self._status == 'working_stop':
            self._change_status('resting')
        elif self._status == 'resting_stop':
            self._change_status('working')
        else:
            self._create_error_change_status_event(self._status, 'unknown')

    def pause(self) -> None:
        """Приостановка текущего таймера"""

        if self._status == 'working':
            self._change_status('working_pause')
        elif self._status == 'resting':
            self._change_status('resting_pause')
        else:
            self._create_error_change_status_event(self._status, 'unknown')

    def resume(self) -> None:
        """Возобновление текущего таймера после приостановки"""

        if self._status == 'working_pause':
            self._change_status('working')
        elif self._status == 'resting_pause':
            self._change_status('resting')
        else:
            self._create_error_change_status_event(self._status, 'unknown')

    def stop(self) -> None:
        """Полная остановка таймера"""

        self._change_status('disabled')

    def _change_status(self, new_status: PomodoroTimerStatus):
        prev_status = self._status

        available_new_statuses = pomodoro_status_to_next_status_map.get(prev_status)

        if new_status != 'disabled' and new_status not in available_new_statuses:
            self._create_error_change_status_event(prev_status, new_status)
        else:
            self._status = new_status
            self._create_change_status_event(prev_status, new_status)

    def _set_total_and_rest_seconds(
            self,
            total: int | None,
            rest: int | None,
    ):
        self._current_timer_total_seconds = total
        self._current_timer_rest_seconds = rest

    def _create_change_status_event(self, prev_status: PomodoroTimerStatus, new_status: PomodoroTimerStatus):
        self._event_bus.publish(
            system_event_types.SystemEvent(
                type='pomodoro_tracker.change_status',
                data=system_event_types.SystemEventPomodoroChangeStatus(
                    prev_status=prev_status,
                    new_status=new_status,
                )
            )
        )

    def _create_error_change_status_event(self, prev_status: PomodoroTimerStatus, new_status: PomodoroTimerStatus):
        self._event_bus.publish(
            system_event_types.SystemEvent(
                type='error.system',
                data=system_event_types.SystemEventAppError(
                    source='PomodoroTracker',
                    error=f'Cant move status: "{prev_status}" -> "{new_status}"',
                )
            )
        )
