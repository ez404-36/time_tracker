import datetime
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Literal

from apps.time_tracker.services.window_control.abstract import WindowData

SystemEventType = Literal[
    'app.open',
    'app.close',
    'app.change_settings',
    'app.update_persistent_store',

    'main_tracker.start',
    'main_tracker.pause',   # Только в таймере Помодоро перед началом следующего таймера или при таймере "Отдых"
    'main_tracker.stop',

    'activity_tracker.start',
    'activity_tracker.stop',
    'activity_tracker.detect_idle',
    'activity_tracker.stop_idle',

    'window_tracker.start',
    'window_tracker.stop',
    'window_tracker.switch_window',
    'window_tracker.change_opened_windows',

    'pomodoro_tracker.start_work',
    'pomodoro_tracker.end_work',
    'pomodoro_tracker.start_rest',
    'pomodoro_tracker.end_rest',

    'tasks.add',
    'tasks.update',
    'tasks.delete',

    'error.wrong_config',
    'error.file_not_found',
]

@dataclass
class SystemEventTimestampData:
    ts: datetime.datetime = datetime.datetime.now(datetime.UTC)


@dataclass
class SystemEventStartMainTracker:
    window_tracking: bool
    idle_tracking: bool
    pomodoro_tracking: bool


@dataclass
class SystemEventSwitchWindowData:
    window: WindowData
    ts: datetime.datetime = datetime.datetime.now(datetime.UTC)


@dataclass
class SystemEventChangeActiveWindowsData:
    active_windows: list[WindowData]


@dataclass
class SystemEventUpdatePersistentStoreData:
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
    | SystemEventUpdatePersistentStoreData

SystemEventCallback = Callable[[SystemEventData], None]


@dataclass
class SystemEvent:
    type: SystemEventType
    data: SystemEventData = field(default_factory=SystemEventTimestampData)
