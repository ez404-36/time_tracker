from typing import Any

import flet as ft

from apps.to_do.controls.todo_mutate_container import ToDoMutateContainer
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
        self._edit_container: ft.Container | None = None
        self._edit_icon: ft.IconButton | None = None
        self._add_children_icon: ft.IconButton | None = None
        self._delete_icon: ft.IconButton | None = None

    def build(self):
        is_done = self._instance.is_done

        self.build_checkbox()
        self.build_edit_container()

        self._edit_icon = ft.IconButton(
            icon=ft.Icons.EDIT,
            on_click=self.on_click_edit,
            visible=not is_done,
            tooltip='Редактировать',
        )
        self._add_children_icon = ft.IconButton(
            icon=ft.Icons.ADD,
            on_click=self.on_click_add_children,
            visible=not is_done,
            tooltip='Добавить вложенную задачу',
        )
        self._delete_icon = ft.IconButton(
            icon=ft.Icons.DELETE,
            on_click=self.on_click_remove,
            icon_color=ft.Colors.RED_300,
            tooltip='Удалить',
        )

        controls: list[Any] = [self._checkbox]

        if not is_done:
            controls.append(self._edit_icon)
            controls.append(self._add_children_icon)

        controls.append(self._edit_container)
        controls.append(self._delete_icon)

        self.controls = controls

    def build_checkbox(self):
        is_done = self._instance.is_done
        color = ft.Colors.GREY if is_done else None
        label = self.get_checkbox_label()

        if not self._checkbox:
            self._checkbox = ft.Checkbox(
                label=label,
                value=is_done,
                on_change=self.on_change_checkbox,
                fill_color=color,
            )
        else:
            self._checkbox.label = label

    def get_checkbox_label(self) -> ft.Row:
        instance = self._instance
        text = ft.Text(instance.title)

        controls = []

        if deadline_str := instance.deadline_str:
            deadline = ft.Text(
                f'[{deadline_str}]',
                weight=ft.FontWeight.W_500
            )
            controls.append(deadline)

        controls.append(text)

        return ft.Row(controls=controls)

    def build_edit_container(self):
        self._edit_container = ToDoMutateContainer(self._instance)

    def on_change_checkbox(self, e):
        is_done = e.control.value
        self._instance.is_done = is_done
        self._instance.save(only=['is_done'])
        refresh_todo_list(self._state, self.__class__)

    def on_click_edit(self, e):
        self._is_editing = True

        self._add_children_icon.visible = False
        self._checkbox.visible = False
        self._delete_icon.visible = False
        self._edit_icon.visible = False
        self._edit_container.visible = True

        self.update()

    def on_stop_editing(self):
        self._instance = ToDo.get(id=self._instance.id)

        for control in self.controls:
            control.visible = not control == self._edit_container

        self.build_checkbox()
        self.update()

    def on_click_add_children(self, e):
        print('Добавить вложенный TODO')

    def on_click_remove(self, e):
        self._instance.delete_instance()
        refresh_todo_list(self._state, self.__class__)
