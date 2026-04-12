from dataclasses import asdict

import flet as ft

from apps.tasks.controls.task_mutate.form import TaskMutateForm
from apps.tasks.helpers import refresh_tasks_tab
from apps.tasks.models import Task
from core.di import container
from core.system_events.types import SystemEvent, SystemEventTaskAction
from ui.base.components.buttons import CancelButton, SaveButton
from ui.utils import show_snackbar


class TaskMutateModal(ft.AlertDialog):
    """
    Модалка создания/изменения объекта ТУДУ
    """

    content: TaskMutateForm

    def __init__(
            self,
            instance: Task | None = None,
            parent_instance: Task | None = None,
            **kwargs,
    ):
        if not parent_instance:
            modal_title = 'Создание задачи' if not instance else f'Редактирование задачи #{instance.id}'
        else:
            modal_title = f'Создание подзадачи к #{parent_instance.id}'

        kwargs.update(
            dict(
                adaptive=True,
                title=ft.Text(modal_title),
            )
        )

        super().__init__(**kwargs)
        self._instance = instance
        self._parent_instance = parent_instance
        self._event_bus = container.event_bus

    def build(self):
        self.content = TaskMutateForm(self._instance, self._parent_instance)

        self.actions = [
            CancelButton(on_click=self._hide),
            SaveButton(on_click=self._on_save),
        ]

    async def _on_save(self):
        form_values = self.content.collect_form_fields()

        if form_values is None:
            show_snackbar('Ошибка при сохранении задачи')
            return

        form_values = asdict(form_values)

        if self._instance:
            for field, value in form_values.items():
                setattr(self._instance, field, value)
            self._instance.save()

            self._event_bus.publish(
                event=SystemEvent(
                    type='tasks.update',
                    data=SystemEventTaskAction(
                        task=str(self._instance)
                    )
                )
            )
        else:
            new_task = Task.create(**form_values)
            self._event_bus.publish(
                event=SystemEvent(
                    type='tasks.add',
                    data=SystemEventTaskAction(
                        task=str(new_task)
                    )
                )
            )

        refresh_tasks_tab()
        self._hide()

    def _hide(self):
        self.open = False
        self.update()
