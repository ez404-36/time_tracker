import asyncio

import flet as ft

from apps.notifications.services.notification_sender import NotificationSender
from apps.to_do.services.deadline_checker import ToDoDeadlineChecker
from core.settings import app_settings


async def check_tasks_deadline(page: ft.Page):
    settings = app_settings
    checker = ToDoDeadlineChecker(settings)

    while True:
        deadlined_tasks = await checker.get_deadlined_right_now()

        if deadlined_tasks:
            if settings.enable_todo_deadline_sound_notifications:
                settings.play_todo_deadline_sound()
            NotificationSender(
                page,
                f'Время выполнить задачи:\n {"\n - ".join([it.title for it in deadlined_tasks])}'
            ).send()

        await asyncio.sleep(60)