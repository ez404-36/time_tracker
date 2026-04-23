from pathlib import Path

_HOME_DIR = Path.home()

USER_DATA_DIR = _HOME_DIR / ".time_tracker"

USER_DATA_DIR.mkdir(parents=True, exist_ok=True)

DB_URL = USER_DATA_DIR / 'database.db'

USER_MEDIA_DIR = USER_DATA_DIR / "media"
USER_AUDIO_DIR = USER_MEDIA_DIR / "audio"

PROJECT_DIR = Path(__file__).parent.parent

MEDIA_DIR = PROJECT_DIR / "media"
ASSETS_DIR = MEDIA_DIR / "assets"
AUDIO_DIR = MEDIA_DIR / "audio"
MIGRATIONS_DIR = PROJECT_DIR / "migrations" / "revisions"

HOURS_PER_DAY = 24
MINUTES_PER_HOUR = 60
SECONDS_PER_MINUTE = 60
