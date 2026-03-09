from pathlib import Path

BASE_DIR = Path(__file__).parent.parent

MEDIA_DIR = BASE_DIR / "media"
AUDIO_DIR = MEDIA_DIR / "audio"
MIGRATIONS_DIR = BASE_DIR / "migrations" / "revisions"
