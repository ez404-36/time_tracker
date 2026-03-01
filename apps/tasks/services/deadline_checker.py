import datetime
from typing import Collection

from peewee import Value

from apps.tasks.models import Task


class TaskDeadlineChecker:
    """
    Проверяет задачи на предмет срока их исполнения.
    """

    @staticmethod
    async def get_expired_tasks(date_time: datetime.datetime) -> Collection[Task]:
        """
        Возвращает задачи, срок исполнения которых прошёл к текущему моменту времени
        """

        _date = date_time.date()
        _time = datetime.time(date_time.hour, date_time.minute, 0)

        return (
            Task.select(
                Task,
                Value(Task.deadline_time == _time).alias('is_expired_at_now'),
            )
            .where(
                Task.is_done == False,
                Task.is_expired == False,
                (Task.deadline_date <= _date) & (Task.deadline_time <= _time)
                 |
                (Task.deadline_date < _date) & (Task.deadline_time == None)
            )
        )
