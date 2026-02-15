import datetime

from peewee import *

from apps.time_tracker.consts import EventType, EventInitiator
from apps.time_tracker.models import Event
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
    enable_todo_sound_deadline_notifications = BooleanField(
        help_text='Включить звуковые уведомления для задач', default=True
    )
    enable_idle_start_sound_notifications = BooleanField(
        help_text='Включить звуковые уведомления о начала бездействия', default=True
    )

    class Meta:
        table_name = 'settings'

    @classmethod
    def get_solo(cls) -> AppSettings:
        return AppSettings.select().first()

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
