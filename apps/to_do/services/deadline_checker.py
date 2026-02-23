import datetime
from typing import Collection

from peewee import Value

from apps.to_do.models import ToDo


class ToDoDeadlineChecker:
    """
    Проверяет ТУДУшки на предмет срока их исполнения.
    """

    @staticmethod
    async def get_expired_todo(date_time: datetime.datetime) -> Collection[ToDo]:
        """
        Возвращает ТУДУ, срок исполнения которых прошёл к текущему моменту времени
        """

        _date = date_time.date()
        _time = datetime.time(date_time.hour, date_time.minute, 0)

        return (
            ToDo.select(
                ToDo,
                Value(ToDo.deadline_time == _time).alias('is_expired_at_now'),
            )
            .where(
                ToDo.is_done == False,
                ToDo.is_expired == False,
                (ToDo.deadline_date <= _date) & (ToDo.deadline_time <= _time)
                 |
                (ToDo.deadline_date < _date) & (ToDo.deadline_time == None)
            )
        )
