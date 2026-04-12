import datetime

from peewee import DateTimeField, IntegerField
from playhouse.sqlite_ext import JSONField

from apps.events.consts import EventActor, EventType
from core.models import BaseModel


class Event(BaseModel):
    """
    Любое событие
    """

    ts = DateTimeField(help_text='Дата и время события (UTC)', default=lambda: datetime.datetime.now(datetime.UTC))
    type = IntegerField(help_text='Тип события', choices=EventType.choices)
    actor = IntegerField(help_text='Инициатор события', choices=EventActor.choices)
    data = JSONField(help_text='Опциональные данные', default=dict)

    class Meta:
        table_name = 'event'
