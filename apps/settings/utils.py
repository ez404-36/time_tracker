import glob
import os

from core.consts import AUDIO_DIR


def get_available_notification_sounds() -> list[str]:
    """
    :return: список названий звуковых сигналов для оповещений
    """

    return list(glob.glob(os.path.join(AUDIO_DIR, "*.*")))
