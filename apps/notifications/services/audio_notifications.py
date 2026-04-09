from core.audio_player import AudioPlayer
from core.consts import AUDIO_DIR
from core.di import container
from core.system_events.types import SystemEvent, SystemEventFileNotFound, SystemEventWrongConfigData


class AudioNotificationService:
    """
    Сервис по отправке звуковых уведомлений
    """

    def __init__(self):
        self._app_settings = container.app_settings
        self._event_bus = container.event_bus

    def play_task_deadline_sound(self):
        if self._app_settings.enable_task_deadline_sound_notifications:
            if task_deadline_sound := self._app_settings.task_deadline_sound:
                self._play_sound(task_deadline_sound)
            else:
                self._event_bus.publish(
                    event=SystemEvent(
                        type='error.wrong_config',
                        data=SystemEventWrongConfigData(
                            field='task_deadline_sound',
                            error='File not specified'
                        )
                    )
                )

    def play_idle_start_sound(self):
        if self._app_settings.enable_idle_start_sound_notifications:
            if idle_start_sound := self._app_settings.idle_start_sound:
                self._play_sound(idle_start_sound)
            else:
                self._event_bus.publish(
                    event=SystemEvent(
                        type='error.wrong_config',
                        data=SystemEventWrongConfigData(
                            field='idle_start_sound',
                            error='File not specified'
                        )
                    )
                )

    def play_pomodoro_sound(self):
        if self._app_settings.enable_pomodoro_sound_notifications:
            if sound := self._app_settings.pomodoro_sound:
                self._play_sound(sound)
            else:
                self._event_bus.publish(
                    event=SystemEvent(
                        type='error.wrong_config',
                        data=SystemEventWrongConfigData(
                            field='pomodoro_sound',
                            error='File not specified'
                        )
                    )
                )

    def _play_sound(self, file_name: str | None):
        if file_name:
            file = AUDIO_DIR / file_name
            if file.exists():
                AudioPlayer.play(file)
            else:
                self._event_bus.publish(
                    event=SystemEvent(
                        type='error.wrong_config',
                        data=SystemEventFileNotFound(
                            file=file
                        )
                    )
                )
