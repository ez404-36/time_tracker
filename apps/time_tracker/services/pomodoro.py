__all__ = (
    'Pomodoro',
    'PomodoroTimerStatus',
)

from typing import Literal

from apps.events.models import Event
from apps.notifications.services.notification_sender import NotificationSender
from apps.events.consts import EventActor, EventType
from core.di import container

PomodoroTimerStatus = Literal[
    'disabled',
    'unknown',
    'working',
    'working_pause',
    'working_stop',
    'resting',
    'resting_pause',
    'resting_stop',
]


pomodoro_status_to_next_status_map: dict[PomodoroTimerStatus, list[PomodoroTimerStatus]] = {
    'disabled': ['working'],
    'working': ['working_pause', 'working_stop'],
    'working_pause': ['working'],
    'working_stop': ['resting'],
    'resting': ['resting_pause', 'resting_stop'],
    'resting_pause': ['resting'],
    'resting_stop': ['working'],
}


class Pomodoro:
    """
    Сервис по взаимодействию с таймером Помодоро.
    Принцип работы: поочередный запуск таймеров работы/отдыха
    """

    def __init__(self):
        self._store = container.session_store
        self._app_settings = container.app_settings
        self._notification_sender = NotificationSender()

        self._status: PomodoroTimerStatus = 'disabled'
        self._store.set('pomodoro', self._status)

        self._current_timer_total_seconds: int | None = None
        self._current_timer_rest_seconds: int | None = None

    @property
    def status(self) -> PomodoroTimerStatus:
        return self._status

    @property
    def is_on_pause(self) -> bool:
        return self._status in ['working_pause', 'resting_pause']

    @property
    def total_seconds(self) -> int | None:
        return self._current_timer_total_seconds

    @property
    def rest_seconds(self) -> int | None:
        return self._current_timer_rest_seconds

    @rest_seconds.setter
    def rest_seconds(self, seconds: int):
        self._current_timer_rest_seconds = seconds

    def start(self) -> None:
        """Первичный запуск работы по таймеру Помодоро"""
        self._change_status('working')
        self._set_total_and_rest_seconds(
            total=self._app_settings.pomodoro_work_time,
            rest=self._app_settings.pomodoro_work_time,
        )

    def stop_current_timer(self):
        """Остановка текущего таймера"""

        if self._status == 'working':
            self._change_status('working_stop')
            self._set_total_and_rest_seconds(total=0, rest=0)
            self._notification_sender.send_info('Время отдохнуть')
        elif self._status == 'resting':
            self._change_status('resting_stop')
            self._notification_sender.send_info('Пора работать')
            self._set_total_and_rest_seconds(total=0, rest=0)
        else:
            self._create_error_change_status_event(self._status, 'unknown')

    def start_next_timer(self):
        """Запуск следующего таймера"""

        if self._status == 'working_stop':
            self._change_status('resting')
            self._current_timer_total_seconds = self._app_settings.pomodoro_rest_time
        elif self._status == 'resting_stop':
            self._change_status('working')
            self._current_timer_total_seconds = self._app_settings.pomodoro_work_time
        else:
            self._create_error_change_status_event(self._status, 'unknown')

    def pause_current_timer(self, rest_seconds: int) -> None:
        """Приостановка текущего таймера"""

        if self._status == 'working':
            self._change_status('working_pause')
            self._current_timer_rest_seconds = rest_seconds
        elif self._status == 'resting':
            self._change_status('resting_pause')
            self._current_timer_rest_seconds = rest_seconds
        else:
            self._create_error_change_status_event(self._status, 'unknown')

    def resume(self) -> None:
        """Возобновление текущего таймера после приостановки"""

        if self._status == 'working_pause':
            self._change_status('working')
            self._current_timer_rest_seconds = 0
        elif self._status == 'resting_pause':
            self._change_status('resting')
            self._current_timer_rest_seconds = 0
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
            self._store.set('pomodoro', self._status)
            self._create_change_status_event(prev_status, new_status)

    def _set_total_and_rest_seconds(
            self,
            total: int | None,
            rest: int | None,
    ):
        self._current_timer_total_seconds = total
        self._current_timer_rest_seconds = rest

    @staticmethod
    def _create_change_status_event(prev_status: PomodoroTimerStatus, new_status: PomodoroTimerStatus):
        Event.create(
            actor=EventActor.USER,
            type=EventType.POMODORO_CHANGE_STATUS,
            data={
                'prev_status': prev_status,
                'new_status': new_status,
            }
        )

    @staticmethod
    def _create_error_change_status_event(prev_status: PomodoroTimerStatus, new_status: PomodoroTimerStatus):
        Event.create(
            type=EventType.APP_ERROR,
            actor=EventActor.SYSTEM,
            data={
                'type': 'Pomodoro',
                'info': f'moving timer status from "{prev_status}" to "{new_status}"',
            }
        )
