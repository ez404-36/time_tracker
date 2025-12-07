from typing import Any

import flet as ft

from apps.to_do.helpers import refresh_todo_list
from apps.to_do.models import ToDo
from core.state import TodoTabState


class ToDoTabToDoRowControl(ft.Row):
    """
    Компонент одной строчки ТУДУ
    """
    def __init__(self, instance: ToDo, state: TodoTabState, **kwargs):
        super().__init__(**kwargs)
        self._instance = instance
        self._state = state
        self._is_editing = False

        self._checkbox: ft.Checkbox | None = None
        self._edit_field: ft.TextField | None = None
        self._edit_icon: ft.IconButton | None = None
        self._add_children_icon: ft.IconButton | None = None
        self._delete_icon: ft.IconButton | None = None

        self.build()

    def build(self):
        is_done = self._instance.is_done

        self.build_checkbox()

        self._edit_icon = ft.IconButton(
            icon=ft.Icons.EDIT,
            on_click=self.on_click_edit,
            disabled=is_done,
        )
        self._add_children_icon = ft.IconButton(
            icon=ft.Icons.ADD,
            on_click=self.on_click_add_children,
            disabled=is_done,
        )
        self._delete_icon = ft.IconButton(
            icon=ft.Icons.DELETE,
            on_click=self.on_click_remove,
            icon_color=ft.Colors.RED_300,
        )

        controls: list[Any] = [self._checkbox]

        if not is_done:
            controls.append(self._edit_icon)
            controls.append(self._add_children_icon)

        controls.append(self._delete_icon)

        self.controls = controls

    def build_checkbox(self):
        is_done = self._instance.is_done
        color = ft.Colors.GREY if is_done else None

        self._checkbox = ft.Checkbox(
            label=self._instance.title,
            value=is_done,
            on_change=self.on_change_checkbox,
            fill_color=color,
        )

    def build_text_field(self):
        self._edit_field = ft.TextField(value=self._instance.title)

    def on_change_checkbox(self, e):
        is_done = e.control.value
        self._instance.is_done = is_done
        self._instance.save(only=['is_done'])
        refresh_todo_list(self._state, self.__class__)

    def on_click_edit(self, e):
        if not self._is_editing:
            # start editing
            self.controls.remove(self._checkbox)
            self.build_text_field()
            self.controls.insert(0, self._edit_field)
            self._edit_icon.icon = ft.Icons.CHECK
        else:
            # submit
            value = self._edit_field.value
            self._instance.title = value
            self._instance.save(only=['title'])
            self.controls.remove(self._edit_field)
            self.build_checkbox()
            self.controls.insert(0, self._checkbox)
            self._edit_icon.icon = ft.Icons.EDIT

        self._is_editing = not self._is_editing

        self._add_children_icon.disabled = self._is_editing
        self._delete_icon.disabled = self._is_editing

        self.update()

    def on_click_add_children(self, e):
        print('Добавить вложенный TODO')

    def on_click_remove(self, e):
        self._instance.delete_instance()
        refresh_todo_list(self._state, self.__class__)
