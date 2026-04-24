import os
import sys
from pathlib import Path

_HOME_DIR = Path.home()

USER_DATA_DIR = _HOME_DIR / ".time_tracker"

DB_URL = USER_DATA_DIR / 'database.db'

USER_MEDIA_DIR = USER_DATA_DIR / "media"
USER_AUDIO_DIR = USER_MEDIA_DIR / "audio"

if getattr(sys, 'frozen', False):
    # Путь к временной папке, созданной PyInstaller
    pyinstaller_dir = os.environ.get('_MEIPASS2', sys._MEIPASS)
    PROJECT_DIR = Path(pyinstaller_dir)
else:
    PROJECT_DIR = Path(__file__).parent.parent

MEDIA_DIR = PROJECT_DIR / "media"
ASSETS_DIR = MEDIA_DIR / "assets"
AUDIO_DIR = MEDIA_DIR / "audio"
MIGRATIONS_DIR = PROJECT_DIR / "migrations" / "revisions"

HOURS_PER_DAY = 24
MINUTES_PER_HOUR = 60
SECONDS_PER_MINUTE = 60
