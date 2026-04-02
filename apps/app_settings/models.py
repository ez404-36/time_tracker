from functools import lru_cache

import pytz
from peewee import BooleanField, CharField, IntegerField, SmallIntegerField

from core.models import BaseModel


class AppSettings(BaseModel):
    """
    Настройки приложения
    """

    # region Общие настройки

    client_timezone = CharField(help_text='Таймзона клиента', default='Europe/Moscow')

    # endregion

    # region Отслеживание активности

    enable_window_tracking = BooleanField(help_text='Включить отслеживание активных окон', default=False)

    enable_idle_tracking = BooleanField(help_text='Включить отслеживание бездействия', default=False)
    idle_threshold = IntegerField(help_text='Порог бездействия (секунд)', default=60)

    enable_pomodoro = BooleanField(help_text='Включить работу по таймеру', default=False)
    pomodoro_work_time = SmallIntegerField(help_text='Время непрерывной работы (минут)', null=True)
    pomodoro_rest_time = SmallIntegerField(help_text='Время отдыха (минут)', null=True)

    # endregion

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


def get_settings() -> AppSettings:
    return AppSettings.get_solo()
