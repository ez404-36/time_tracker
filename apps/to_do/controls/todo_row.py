from typing import Any

import flet as ft

from apps.to_do.helpers import refresh_todo_list
from apps.to_do.models import ToDo
from core.state import TodoTabState


class ToDoTabToDoRowControl(ft.Row):
    def __init__(self, instance: ToDo, state: TodoTabState, **kwargs):
        super().__init__(**kwargs)
        self._instance = instance
        self._state = state

        is_done = self._instance.is_done
        color = ft.Colors.GREY if is_done else None

        checkbox = ft.Checkbox(
            label=self._instance.title,
            value=is_done,
            on_change=self.on_change_checkbox,
            fill_color=color,
        )
        add_children_icon = ft.IconButton(
            icon=ft.Icons.ADD,
            on_click=self.on_click_add_children,
            disabled=is_done,
        )
        delete_icon = ft.IconButton(
            icon=ft.Icons.DELETE,
            on_click=self.on_click_remove,
            icon_color=ft.Colors.RED_300,
        )

        controls: list[Any] = [checkbox]

        if not is_done:
            controls.append(add_children_icon)

        controls.append(delete_icon)

        self.controls = controls

    def on_change_checkbox(self, e):
        is_done = e.control.value
        self._instance.is_done = is_done
        self._instance.save(only=['is_done'])
        refresh_todo_list(self._state, self.__class__)

    def on_click_add_children(self, e):
        print('Добавить вложенный TODO')

    def on_click_remove(self, e):
        self._instance.delete()
        refresh_todo_list(self._state, self.__class__)
