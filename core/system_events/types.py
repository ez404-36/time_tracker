import datetime
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Literal

from apps.time_tracker.services.window_control.abstract import WindowData

SystemEventType = Literal[
    'app.open',
    'app.close',
    'app.change_settings',
    'app.wrong_config',
    'app.file_not_found',

    'tracker.start',
    'tracker.stop',
    'tracker.detect_idle',
    'tracker.stop_idle',
    'tracker.switch_window',
    'tracker.change_opened_windows',

    'tasks.add',
    'tasks.update',
    'tasks.delete',
]

@dataclass
class SystemEventTimestampData:
    ts: datetime.datetime = datetime.datetime.now(datetime.UTC)


@dataclass
class SystemEventSwitchWindowData:
    window: WindowData
    ts: datetime.datetime = datetime.datetime.now(datetime.UTC)


@dataclass
class SystemEventChangeActiveWindowsData:
    active_windows: list[WindowData]


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
    | SystemEventChangeSettingsData \
    | SystemEventSwitchWindowData \
    | SystemEventChangeActiveWindowsData \
    | SystemEventWrongConfigData \
    | SystemEventFileNotFound \
    | SystemEventTaskAction \
    | Any

SystemEventCallback = Callable[[SystemEventData], None]


@dataclass
class SystemEvent:
    type: SystemEventType
    data: SystemEventData = field(default_factory=SystemEventTimestampData)
