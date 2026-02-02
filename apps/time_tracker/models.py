__all__ = (
    'PomodoroTimer',
    'Event',
    'WindowSession',
    'IdleSession',
)

import datetime
from typing import TYPE_CHECKING

from peewee import *
from playhouse.sqlite_ext import JSONField

from apps.time_tracker.consts import EventType
from core.models import BaseModel


class PomodoroTimer(BaseModel):
    """
    Таймер помидора (работа/отдых)
    """

    title = CharField(unique=True, max_length=50)
    work_time = SmallIntegerField(help_text='Время непрерывной работы (минут)')
    rest_time = SmallIntegerField(help_text='Время отдыха (минут)')

    class Meta:
        table_name = 'pomodoro_timer'

    if TYPE_CHECKING:
        title: str
        work_time: int | None
        rest_time: int | None


class Event(BaseModel):
    """
    Любое событие
    """

    ts = DateTimeField(help_text='Дата и время события (UTC)', default=lambda _: datetime.datetime.now(datetime.UTC))
    type = IntegerField(help_text='Тип события', choices=EventType.choices)
    data = JSONField(help_text='Опциональные данные', default=dict)

    class Meta:
        table_name = 'event'


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

    app_name = CharField(help_text='Название приложения')
    window_title = CharField(help_text='Заголовок окна', null=True)

    class Meta:
        table_name = 'window_session'


class IdleSession(SessionAbstract):
    """
    Периоды бездействия
    """

    class Meta:
        table_name = 'idle_session'
