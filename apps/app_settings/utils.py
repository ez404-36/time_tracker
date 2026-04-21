import glob
import os

from core.consts import AUDIO_DIR, USER_AUDIO_DIR


def get_available_notification_sounds() -> list[str]:
    """
    :return: список названий звуковых сигналов для оповещений
    """

    audio_dirs = [AUDIO_DIR, USER_AUDIO_DIR]

    sounds = []

    for audio_dir in audio_dirs:
        sounds.extend(glob.glob(os.path.join(audio_dir, "*.*")))

    return sounds
