import platform
import os
import subprocess
from typing import Literal, cast

AvailableOS = Literal[
    'Linux',
    'Windows',
    'Darwin',
]

# Параметры ОС
PLATFORM: AvailableOS = cast(AvailableOS, platform.system())

if PLATFORM == 'Linux':
    _display_system = os.environ.get("XDG_SESSION_TYPE")
    USE_X11 = _display_system == 'x11'
    USE_WAYLAND = _display_system == 'wayland'
else:
    USE_X11 = False
    USE_WAYLAND = False


try:
    subprocess.check_output(['ffmpeg', '-version'])
except Exception as e:
    IS_FFMPEG_INSTALLED = False
else:
    IS_FFMPEG_INSTALLED = True

# Визаульные настройки

SNACKBAR_DURATION_SECONDS = 3

DATE_FORMAT = '%d.%m.%y'
TIME_FORMAT = '%H:%M'
TIME_WITH_SECONDS_FORMAT = '%H:%M:%S'
