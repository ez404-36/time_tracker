from typing import Literal

from apps.time_tracker.models import IdleSession, WindowSession

AnySession = WindowSession | IdleSession

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
