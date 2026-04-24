import asyncio
import datetime

from apps.notifications.services.audio_notifications import AudioNotificationService
from apps.notifications.services.notification_sender import NotificationSender
from apps.tasks.helpers import refresh_tasks_tab
from apps.tasks.models import Task
from apps.tasks.services.deadline_checker import TaskDeadlineChecker


class TaskDeadlineHandler:
    def __init__(self):
        self.checker = TaskDeadlineChecker()
        self.notification_sender = NotificationSender()
        self.audio_notification_sender = AudioNotificationService()

    async def run(self):
        while True:
            now = datetime.datetime.now()
            expired_tasks = await self.checker.get_expired_tasks(now)

            if expired_tasks:
                self.audio_notification_sender.play_task_deadline_sound()

                expired_at_now = []
                expired_before = []

                for task in expired_tasks:
                    if task.is_expired_at_now:
                        expired_at_now.append(task)
                    else:
                        expired_before.append(task)

                if expired_at_now:
                    self.notification_sender.send_error(
                        f'Время выполнить задачи:\n{self._pretty_task_list(expired_at_now)}'
                    )

                if expired_before:
                    Task.update(is_expired=True).where(Task.id in [it.id for it in expired_before]).execute()

                    self.notification_sender.send_error(
                        f'Просрочен срок исполнения следующих задач:\n{self._pretty_task_list(expired_before)}'
                    )

                    refresh_tasks_tab(with_update_controls=True)

            await asyncio.sleep(60)

    @staticmethod
    def _pretty_task_list(task_list: list[Task]) -> str:
        return f' - {"\n - ".join([it.title for it in task_list])}'
