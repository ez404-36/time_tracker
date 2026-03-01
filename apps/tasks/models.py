__all__ = (
    'Task',
)

import datetime
from typing import Self

from peewee import *

from core.models import BaseModel


class Task(BaseModel):
    """
    Задача
    """

    title: str = CharField(max_length=50, help_text='Название задачи')
    description: str = TextField(null=True, help_text='Описание задачи')
    created_at = DateTimeField(default=lambda: datetime.datetime.now(datetime.UTC))
    parent: Self | None = ForeignKeyField('self', null=True, backref='children')
    deadline_date: datetime.date | None = DateField(null=True, help_text='Дедлайн (дата)')
    deadline_time: datetime.time | None = TimeField(null=True, help_text='Дедлайн (время)')
    is_done: bool = BooleanField(default=False, help_text='Готово')
    is_expired: bool = BooleanField(default=False, help_text='Просрочено')

    class Meta:
        table_name = 'task'

    def __str__(self):
        return f'(#{self.id}) {self.title}'

    @property
    def deadline_date_str(self) -> str:
        deadline_date = self.deadline_date
        return deadline_date.strftime("%d.%m.%Y") if deadline_date else ''

    @property
    def deadline_time_str(self) -> str:
        deadline_time = self.deadline_time
        return deadline_time.strftime('%H:%M') if deadline_time else ''

    @property
    def deadline_str(self) -> str:
        return ' '.join(
            it for it in [self.deadline_date_str, self.deadline_time_str] if it
        )

