from pathlib import Path

BASE_DIR = Path(__file__).parent.parent

MEDIA_DIR = BASE_DIR / "media"
AUDIO_DIR = MEDIA_DIR / "audio"
MIGRATIONS_DIR = BASE_DIR / "migrations" / "revisions"


HOURS_PER_DAY = 24
MINUTES_PER_HOUR = 60
SECONDS_PER_MINUTE = 60
