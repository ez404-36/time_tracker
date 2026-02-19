import datetime
from functools import lru_cache

from peewee import *
from playsound3 import playsound

from apps.time_tracker.consts import EventType, EventInitiator
from apps.time_tracker.models import Event
from core.consts import AUDIO_DIR
from core.models import BaseModel


def get_client_timezone_offset() -> int:
    now_hour = datetime.datetime.now().hour
    now_utc_hour = datetime.datetime.now(datetime.timezone.utc).hour

    offset = now_hour - now_utc_hour
    return offset


class AppSettings(BaseModel):
    """
    Настройки приложения
    """

    client_timezone = DecimalField(
        help_text='Таймзона клиента',
        max_digits=2,
        decimal_places=2,
        default=lambda: get_client_timezone_offset()
    )
    idle_threshold = IntegerField(help_text='Порог бездействия (секунд)', default=60)
    enable_pomodoro = BooleanField(help_text='Включить работу по таймеру', default=False)
    pomodoro_work_time = SmallIntegerField(help_text='Время непрерывной работы (минут)', null=True)
    pomodoro_rest_time = SmallIntegerField(help_text='Время отдыха (минут)', null=True)

    # region Звуковые уведомления

    enable_todo_deadline_sound_notifications = BooleanField(
        help_text='Включить звуковые уведомления для дедлайна задач', default=False
    )
    todo_deadline_sound = CharField(
        help_text='Название файла звукового уведомления для дедлайна задач', null=True, max_length=255
    )
    enable_idle_start_sound_notifications = BooleanField(
        help_text='Включить звуковые уведомления о начала бездействия', default=False
    )
    idle_start_sound = CharField(
        help_text='Название файла звукового уведомления о начале бездействия', null=True, max_length=255
    )

    # endregion

    class Meta:
        table_name = 'settings'

    @classmethod
    @lru_cache(maxsize=1)
    def get_solo(cls) -> AppSettings:
        app_settings, _ = AppSettings.get_or_create()
        return app_settings

    def detect_and_update_client_timezone(self):
        client_timezone = get_client_timezone_offset()
        if client_timezone != self.client_timezone:
            self.client_timezone = client_timezone
            self.save(only=['client_timezone'])
            Event.create(
                type=EventType.CHANGE_SETTINGS,
                initiator=EventInitiator.SYSTEM,
                data={'client_timezone': self.client_timezone}
            )

    def play_todo_deadline_sound(self):
        if self.enable_todo_deadline_sound_notifications:
            if self.todo_deadline_sound:
                self._play_sound(self.todo_deadline_sound)
            else:
                Event.create(
                    type=EventType.WRONG_CONFIG,
                    initiator=EventInitiator.SYSTEM,
                    data={
                        'todo_deadline_sound': 'File not specified',
                    }
                )

    def play_idle_start_sound(self):
        if self.enable_idle_start_sound_notifications:
            if self.idle_start_sound:
                self._play_sound(self.idle_start_sound)
            else:
                Event.create(
                    type=EventType.WRONG_CONFIG,
                    initiator=EventInitiator.SYSTEM,
                    data={
                        'idle_start_sound': 'File not specified',
                    }
                )

    @staticmethod
    def _play_sound(file_name: str | None):
        if file_name:
            file = AUDIO_DIR / file_name
            if file.exists():
                playsound(file)
            else:
                Event.create(
                    type=EventType.FILE_NOT_FOUND,
                    initiator=EventInitiator.SYSTEM,
                    data={
                        'file': file,
                    }
                )
