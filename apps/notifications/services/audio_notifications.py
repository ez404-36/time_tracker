from pathlib import Path

from apps.app_settings.models import SettingsAudioParam
from core.audio_player import AudioPlayer
from core.consts import AUDIO_DIR
from core.di import container
from core.system_events.types import SystemEvent, SystemEventFileInfo


class AudioNotificationService:
    """
    Сервис по отправке звуковых уведомлений
    """

    def __init__(self):
        self._app_settings = container.app_settings
        self._event_bus = container.event_bus

    def play_task_deadline_sound(self):
        self._play_sound(self._app_settings.task_deadline_sound_config)

    def play_idle_start_sound(self):
        self._play_sound(self._app_settings.idle_sound_config)

    def play_pomodoro_sound(self):
        self._play_sound(self._app_settings.pomodoro_sound_config)

    def _play_sound(self, audio_param: SettingsAudioParam | None):
        if not audio_param or audio_param.disabled:
            return

        if file_name := audio_param.sound:
            file = AUDIO_DIR / file_name
            if file.exists():
                AudioPlayer.play(file, volume_offset=audio_param.volume_offset)
            else:
                self._on_file_not_found(file)

    def _on_file_not_found(self, file: str | Path):
        self._event_bus.publish(
            event=SystemEvent(
                type='error.wrong_config',
                data=SystemEventFileInfo(
                    filename=Path(file).name,
                    path=file,
                )
            )
        )
