from functools import lru_cache

import pytz
from playhouse.sqlite_ext import JSONField
from peewee import BooleanField, CharField, DecimalField, ForeignKeyField, IntegerField, SmallIntegerField

from core.models import BaseModel


class SettingsAudioParam(BaseModel):
    """
    Параметр настройки звука для какого-либо действия
    """
    disabled = BooleanField(default=False)
    sound = CharField(help_text='Название звукового файла', null=True, max_length=255)
    volume_offset = DecimalField(
        help_text='Смещение уровня звука, в децибелах',
        max_digits=3,
        decimal_places=1,
        default=0.0,
    )

    class Meta:
        table_name = 'settings_audio_param'


class AppSettings(BaseModel):
    """
    Настройки приложения
    """

    # region Общие настройки

    client_timezone = CharField(help_text='Таймзона клиента', default='Europe/Moscow')

    # endregion

    ui_settings = JSONField(
        help_text='Визуальные настройки',
        default=dict
    )

    # region Отслеживание активности

    enable_window_tracking = BooleanField(help_text='Включить отслеживание активных окон', default=False)

    enable_idle_tracking = BooleanField(help_text='Включить отслеживание бездействия', default=False)
    idle_threshold = IntegerField(help_text='Порог бездействия (секунд)', default=60)

    enable_pomodoro = BooleanField(help_text='Включить работу по таймеру', default=False)
    pomodoro_work_time = SmallIntegerField(help_text='Время непрерывной работы (минут)', null=True)
    pomodoro_rest_time = SmallIntegerField(help_text='Время отдыха (минут)', null=True)

    # endregion

    # region Звуковые уведомления

    task_deadline_sound_config = ForeignKeyField(SettingsAudioParam, null=True, backref='task_deadline_sound_config')
    idle_sound_config = ForeignKeyField(SettingsAudioParam, null=True, backref='idle_sound_config')
    pomodoro_sound_config = ForeignKeyField(SettingsAudioParam, null=True, backref='pomodoro_sound_config')

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
