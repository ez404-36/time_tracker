import flet as ft

from apps.to_do.controls.todo_mutate_container import ToDoMutateContainer
from apps.to_do.helpers import refresh_todo_list
from core.state import State, TodoTabState


class TodoTabViewControl(ft.Container):
    parent: ft.Tab
    content: ft.Column

    def __init__(self, state: State, **kwargs):
        kwargs.setdefault('padding', 20)
        super().__init__(**kwargs)
        self._state: TodoTabState = state['tabs']['todo']

        self._list_active: ft.Column | None = None
        self._list_done: ft.Column | None = None

    def build(self):
        self._list_active = ft.Column(height=300, scroll=ft.ScrollMode.ADAPTIVE)
        self._list_done = ft.Column(height=300, scroll=ft.ScrollMode.ADAPTIVE)

        self._state['controls']['list_active'] = self._list_active
        self._state['controls']['list_done'] = self._list_done

        refresh_todo_list(self._state, with_update_controls=False)

        self.content = ft.Column(
            controls=[
                ToDoMutateContainer(self._state),
                self._list_active,
                ft.Divider(),
                ft.Text('Завершено'),
                self._list_done,
            ]
        )
