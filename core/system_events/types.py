import datetime
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Awaitable, Callable, Literal, Self

from apps.time_tracker.services.window_control.abstract import WindowData
from apps.time_tracker.types import PomodoroTimerStatus

SystemEventType = Literal[
    'app.open',
    'app.close',
    'app.change_settings',
    'app.update_session_store',

    'main_tracker.start',
    'main_tracker.pause',
    'main_tracker.hold',
    'main_tracker.resume',
    'main_tracker.stop',

    'activity_tracker.start',
    'activity_tracker.stop',
    'activity_tracker.detect_idle',
    'activity_tracker.stop_idle',

    'window_tracker.start',
    'window_tracker.stop',
    'window_tracker.switch_window',
    'window_tracker.change_opened_windows',

    'pomodoro_tracker.change_status',

    'tasks.add',
    'tasks.update',
    'tasks.delete',

    'error.system',
    'error.wrong_config',
    'error.file_not_found',
]

@dataclass
class SystemEventTimestampData:
    ts: datetime.datetime = field(default_factory=lambda: datetime.datetime.now(datetime.UTC))


@dataclass
class SystemEventStartMainTracker:
    window_tracking: bool
    idle_tracking: bool
    pomodoro_tracking: bool

    @classmethod
    def default(cls) -> 'Self':
        return cls(
            window_tracking=False,
            idle_tracking=False,
            pomodoro_tracking=False,
        )


@dataclass
class SystemEventSwitchWindowData:
    window: WindowData
    ts: datetime.datetime = field(default_factory=lambda: datetime.datetime.now(datetime.UTC))


@dataclass
class SystemEventChangeActiveWindowsData:
    active_windows: list[WindowData]


@dataclass
class SystemEventPomodoroChangeStatus:
    prev_status: PomodoroTimerStatus
    new_status: PomodoroTimerStatus


@dataclass
class SystemEventUpdateSessionStoreData:
    key: str
    value: str


@dataclass
class SystemEventChangeSettingsData:
    values: dict[str, Any]


@dataclass
class SystemEventWrongConfigData:
    field: str
    error: str


@dataclass
class SystemEventFileNotFound:
    file: str | Path


@dataclass
class SystemEventAppError:
    source: str
    error: str


@dataclass
class SystemEventTaskAction:
    task: str


SystemEventData = SystemEventTimestampData \
                  | SystemEventStartMainTracker \
                  | SystemEventChangeSettingsData \
                  | SystemEventSwitchWindowData \
                  | SystemEventChangeActiveWindowsData \
                  | SystemEventWrongConfigData \
                  | SystemEventFileNotFound \
                  | SystemEventTaskAction \
                  | SystemEventUpdateSessionStoreData \
                  | SystemEventAppError \
                  | SystemEventPomodoroChangeStatus

SyncCallback = Callable[..., None]
AsyncCallback = Callable[..., Awaitable[None]]

SystemEventCallback = SyncCallback | AsyncCallback

@dataclass
class SystemEvent:
    type: SystemEventType
    data: SystemEventData = field(default_factory=SystemEventTimestampData)
