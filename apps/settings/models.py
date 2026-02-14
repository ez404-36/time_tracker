from peewee import *

from core.models import BaseModel


class AppSettings(BaseModel):
    """
    Настройки приложения
    """

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