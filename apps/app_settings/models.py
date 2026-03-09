from functools import lru_cache

import pytz
from peewee import IntegerField, BooleanField, SmallIntegerField, CharField
from playsound3 import playsound

from apps.time_tracker.consts import EventType, EventInitiator
from apps.time_tracker.models import Event
from core.consts import AUDIO_DIR
from core.models import BaseModel


class AppSettings(BaseModel):
    """
    Настройки приложения
    """

    client_timezone = CharField(help_text='Таймзона клиента', default='Europe/Moscow')
    idle_threshold = IntegerField(help_text='Порог бездействия (секунд)', default=60)
    enable_pomodoro = BooleanField(help_text='Включить работу по таймеру', default=False)
    pomodoro_work_time = SmallIntegerField(help_text='Время непрерывной работы (минут)', null=True)
    pomodoro_rest_time = SmallIntegerField(help_text='Время отдыха (минут)', null=True)

    # region Звуковые уведомления

    enable_task_deadline_sound_notifications = BooleanField(
        help_text='Включить звуковые уведомления для дедлайна задач', default=False
    )
    task_deadline_sound = CharField(
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
    def get_solo(cls) -> 'AppSettings':
        app_settings, _ = AppSettings.get_or_create()
        return app_settings

    def get_tz(self) -> pytz.BaseTzInfo:
        return pytz.timezone(self.client_timezone)

    def play_task_deadline_sound(self):
        if self.enable_task_deadline_sound_notifications:
            if self.task_deadline_sound:
                self._play_sound(self.task_deadline_sound)
            else:
                Event.create(
                    type=EventType.WRONG_CONFIG,
                    initiator=EventInitiator.SYSTEM,
                    data={
                        'task_deadline_sound': 'File not specified',
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
