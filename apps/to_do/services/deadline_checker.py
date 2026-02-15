import datetime
from typing import Collection

from apps.to_do.models import ToDo
from core.settings import app_settings


class ToDoDeadlineChecker:
    """
    Проверяет ТУДУшки на предмет срока их исполнения
    """

    def __init__(self):
        self._app_settings = app_settings

    async def get_deadlined_right_now(self) -> Collection[ToDo]:
        """
        Возвращает ТУДУ, срок исполнения которых наступил прямо сейчас
        """
        now = datetime.datetime.now()
        now_date = now.date()
        now_time = now.time()

        return (
            ToDo.select()
            .where(
                ToDo.is_done == False,
                ToDo.deadline_date == now_date,
                ToDo.deadline_time == now_time,
            )
        )