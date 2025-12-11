from typing import Self

import flet as ft

from apps.to_do.controls.todo_add_input import ToDoAddInput
from apps.to_do.controls.todo_add_submit_button import ToDoAddSubmitButton
from apps.to_do.controls.todo_row import ToDoTabToDoRowControl
from apps.to_do.helpers import refresh_todo_list
from apps.to_do.models import ToDo
from core.controls.base_control import BaseControl
from core.state import State, TodoTabState


def refresh_db_todos(state: TodoTabState) -> dict[int, ToDo]:
    state['db']['todos'] = {
        it.id: it
        for it in ToDo.select()
    }
    return state['db']['todos']


class TodoTabControl(BaseControl):
    def __init__(self, state: State):
        super().__init__(state)
        self._state: TodoTabState = state['tabs']['todo']

    @property
    def component(self) -> ft.Container:
        return self._state['controls']['tab']

    def build(self) -> Self:
        self._state['controls']['list_active'] = ft.Column()
        self._state['controls']['list_done'] = ft.Column()

        refresh_todo_list(self._state, ToDoTabToDoRowControl, with_update_controls=False)

        self._state['controls']['submit'] = ToDoAddSubmitButton(self._state)
        self._state['controls']['input'] = ToDoAddInput(self._state)

        self._state['controls']['view'] = ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        self._state['controls']['input'],
                        self._state['controls']['submit'],
                    ]
                ),
                ft.Container(padding=10),
                self._state['controls']['list_active'],
                ft.Divider(),
                ft.Text('Завершено'),
                self._state['controls']['list_done'],
            ]
        )

        self._state['controls']['tab'] = ft.Container(
            padding=20,
            content=self._state['controls']['view'],
        )

        return self
