import asyncio
import datetime

import flet as ft

from apps.notifications.services.notification_sender import NotificationSender
from apps.to_do.models import ToDo
from apps.to_do.services.deadline_checker import ToDoDeadlineChecker
from core.settings import AppSettings


async def check_tasks_deadline(page: ft.Page):
    settings = AppSettings.get_solo()
    checker = ToDoDeadlineChecker()
    notification_sender = NotificationSender(page)

    while True:
        now = datetime.datetime.now()
        expired_tasks = await checker.get_expired_todo(now)

        if expired_tasks:
            settings.play_todo_deadline_sound()

            expired_at_now = []
            expired_before = []

            for task in expired_tasks:
                if task.is_expired_at_now:
                    expired_at_now.append(task)
                else:
                    expired_before.append(task)

            if expired_at_now:
                notification_sender.send(
                    f'Время выполнить задачи:\n{_pretty_task_list(expired_at_now)}'
                )

            if expired_before:

                ToDo.update(is_expired=True).where(ToDo.id in [it.id for it in expired_before]).execute()

                notification_sender.send(
                    f'Просрочен срок исполнения следующих задач:\n{_pretty_task_list(expired_before)}'
                )

        await asyncio.sleep(60)


def _pretty_task_list(task_list: list[ToDo]) -> str:
    return f' - {"\n - ".join([it.title for it in task_list])}'

