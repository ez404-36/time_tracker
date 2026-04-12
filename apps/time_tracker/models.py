__all__ = (
    'WindowSession',
    'IdleSession',
)

import datetime

from peewee import *

from apps.time_tracker.utils import get_app_name_and_transform_window_title
from core.models import BaseModel


class SessionAbstract(BaseModel):
    start_ts = DateTimeField(help_text='Дата и время начала сессии')
    end_ts = DateTimeField(help_text='Дата и время окончания сессии', null=True)
    duration = IntegerField(help_text='Время бездействия', default=0)

    class Meta:
        abstract = True

    def stop(self, ts: datetime.datetime):
        self.end_ts = ts
        self.duration = (ts - self.start_ts).seconds
        self.save(only=['end_ts', 'duration'])


class WindowSession(SessionAbstract):
    """
    Данные о сессии в конкретном окне
    """

    executable_name = CharField(help_text='Название исполняемого файла')
    executable_path = CharField(help_text='Путь до исполняемого файла', null=True)
    window_title = CharField(help_text='Заголовок окна', null=True)

    class Meta:
        table_name = 'window_session'

    @property
    def app_name(self) -> str:
        return get_app_name_and_transform_window_title(self.executable_name, self.window_title)[0]


class IdleSession(SessionAbstract):
    """
    Периоды бездействия
    """

    class Meta:
        table_name = 'idle_session'
