import datetime
from typing import Collection

from apps.settings.models import AppSettings
from apps.to_do.models import ToDo


class ToDoDeadlineChecker:
    """
    Проверяет ТУДУшки на предмет срока их исполнения
    """

    def __init__(self, settings: AppSettings):
        self._app_settings = settings

    async def get_deadlined_right_now(self) -> Collection[ToDo]:
        """
        Возвращает ТУДУ, срок исполнения которых наступил прямо сейчас
        """
        now = datetime.datetime.now()
        now_date = now.date()
        now_time = datetime.time(now.hour, now.minute, 0)

        return (
            ToDo.select()
            .where(
                ToDo.is_done == False,
                ToDo.deadline_date == now_date,
                ToDo.deadline_time == now_time,
            )
        )