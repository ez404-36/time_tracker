import flet as ft

from apps.to_do.controls.todo_mutate_modal import ToDoMutateModal
from apps.to_do.helpers import refresh_todo_list
from apps.to_do.models import ToDo
from core.state import TodoTabState
from ui.consts import Colors, Icons


class ToDoListItem(ft.ListTile):
    """
    Отображение одной задачи
    """

    def __init__(self, state: TodoTabState, instance: ToDo, **kwargs):
        kwargs.update(
            dict(
                width=400,
            )
        )

        super().__init__(**kwargs)
        self._state = state
        self._instance = instance

    def build(self):
        is_done = self._instance.is_done

        self.leading = ft.Checkbox(
            value=is_done,
            fill_color=Colors.GREY if is_done else None,
            on_change=self._on_change_checkbox,
        )

        self.title = ft.Text(
            value=str(self._instance),
        )

        self.subtitle = ft.Text(
            value=self._instance.description,
        )

        self.trailing = ft.PopupMenuButton(
            icon=Icons.MORE_ACTIONS,
            items=[
                ft.PopupMenuItem(
                    icon=Icons.EDIT,
                    content='Редактировать',
                    on_click=lambda e: self.page.show_dialog(ToDoMutateModal(self._state, instance=self._instance)),
                ),
                ft.PopupMenuItem(
                    icon=Icons.ADD,
                    content='Добавить вложенную задачу',
                    on_click=lambda e: self.page.show_dialog(ToDoMutateModal(self._state, parent_instance=self._instance)),
                ),
                ft.PopupMenuItem(
                    icon=Icons.DELETE,
                    content='Удалить',
                    on_click=self._on_click_delete,
                )
            ]
        )

    def _on_change_checkbox(self, e):
        is_done = e.control.value
        self._instance.is_done = is_done
        self._instance.save(only=['is_done'])
        refresh_todo_list(self._state)

    def _on_click_delete(self, e):
        self._instance.delete_instance()
        refresh_todo_list(self._state)