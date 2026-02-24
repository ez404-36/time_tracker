from dataclasses import asdict

import flet as ft

from apps.to_do.controls.todo_mutate_form import TodoMutateForm
from apps.to_do.helpers import refresh_todo_list
from apps.to_do.models import ToDo
from core.state import TodoTabState


class ToDoMutateModal(ft.AlertDialog):
    """
    Модалка создания/изменения объекта ТУДУ
    """

    content: TodoMutateForm

    def __init__(
            self,
            state: TodoTabState,
            instance: ToDo | None = None,
            parent_instance: ToDo | None = None,
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
        self._state = state
        self._instance = instance
        self._parent_instance = parent_instance

    def build(self):
        self.content = TodoMutateForm(self._instance, self._parent_instance)

        self.actions = [
            ft.TextButton('Отмена', on_click=lambda e: self.page.pop_dialog()),
            ft.TextButton('Сохранить', on_click=self._on_save)
        ]

    def _on_save(self):
        form_values = asdict(self.content.collect_form_fields())

        if self._instance:
            for field, value in form_values.items():
                setattr(self._instance, field, value)
        else:
            ToDo.create(**form_values)

        refresh_todo_list(self._state)
        self.page.pop_dialog()