import flet as ft

from apps.to_do.controls.todo_row import ToDoTabToDoRowControl
from apps.to_do.helpers import refresh_todo_list
from apps.to_do.models import ToDo
from core.state import TodoTabState


class ToDoAddSubmitButton(ft.TextButton):
    """
    Компонент кнопки добавления нового ТУДУ
    """

    def __init__(self, state: TodoTabState, **kwargs):
        kwargs.setdefault('disabled', True)
        kwargs.setdefault('text', 'Добавить')
        super().__init__(**kwargs)
        self._state: TodoTabState = state

    def on_click(self):
        todo_title = self._state['controls']['input'].value

        ToDo.create(title=todo_title)
        refresh_todo_list(self._state, ToDoTabToDoRowControl)

        self._state['controls']['input'].value = ''
        self._state['controls']['view'].update()
