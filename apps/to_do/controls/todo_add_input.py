import flet as ft

from core.state import TodoTabState


class ToDoAddInput(ft.TextField):
    """
    Компонент инпута добавления нового ТУДУ
    """

    def __init__(self, state: TodoTabState, **kwargs):
        kwargs.setdefault('hint_text', 'Не забыть сделать')
        super().__init__(**kwargs)
        self._state = state

    def on_change(self):
        self._state['controls']['submit'].disabled = not self.value
        self._state['controls']['submit'].update()
