__all__ = (
    'ToDo',
)

import datetime

from peewee import *

from core.models import BaseModel


class ToDo(BaseModel):
    """
    Пункт "что сделать ?"
    """

    title = CharField(max_length=50)
    created_at = DateTimeField(default=datetime.datetime.now)
    parent = ForeignKeyField('self', null=True, backref='children')
    deadline = DateTimeField(null=True, help_text='Дедлайн')
    is_done = BooleanField(default=False, help_text='Готово')

    class Meta:
        table_name = 'todo'
