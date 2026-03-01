from dataclasses import asdict

import flet as ft

from apps.tasks.controls.task_mutate_form import TaskMutateForm
from apps.tasks.helpers import refresh_tasks_tab
from apps.tasks.models import Task
from ui.base.components.buttons import CancelButton, SaveButton


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

    def build(self):
        self.content = TaskMutateForm(self._instance, self._parent_instance)

        self.actions = [
            CancelButton(on_click=lambda e: self.page.pop_dialog()),
            SaveButton(on_click=self._on_save),
        ]

    def _on_save(self):
        form_values = asdict(self.content.collect_form_fields())

        if self._instance:
            for field, value in form_values.items():
                setattr(self._instance, field, value)
            self._instance.save()
        else:
            Task.create(**form_values)

        refresh_tasks_tab(self.page)
        self.page.pop_dialog()
