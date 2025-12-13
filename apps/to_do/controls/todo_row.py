from typing import Any

import flet as ft
from flet.core.margin import Margin

from apps.to_do.controls.todo_mutate_container import ToDoMutateContainer
from apps.to_do.helpers import refresh_todo_list
from apps.to_do.models import ToDo
from core.state import TodoTabState


class ToDoRowViewControl(ft.Container):
    """
    Компонент отображения одного ТУДУ
    """

    def __init__(self, instance: ToDo, state: TodoTabState, **kwargs):
        has_parent = instance.parent_id is not None
        if has_parent:
            kwargs.setdefault('margin', Margin(left=50, top=0, bottom=0, right=0))
        kwargs.setdefault('visible', not has_parent or instance.parent_id in state['expanded'])
        super().__init__(**kwargs)
        self._instance = instance
        self._state = state
        self._has_children = self._instance.children.exists()

        self._checkbox: ft.Checkbox | None = None
        self._text: ft.Row | None = None
        self._expand_children_icon: ft.IconButton | None = None
        self._edit_container: ft.Container | None = None
        self._edit_icon: ft.IconButton | None = None
        self._add_children_icon: ft.IconButton | None = None
        self._delete_icon: ft.IconButton | None = None

    @property
    def is_expanded(self) -> bool:
        return self._instance.id in  self._state['expanded']

    def build(self):
        is_done = self._instance.is_done

        self.build_checkbox()
        self.build_expand_children_icon()
        self.build_text()
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

        if self._has_children:
            controls.append(self._expand_children_icon)

        controls.append(self._text)

        if not is_done:
            controls.append(self._edit_icon)
            if not self._instance.parent_id:
                controls.append(self._add_children_icon)

        controls.append(self._edit_container)
        controls.append(self._delete_icon)

        self.content = ft.Row(controls)

    def build_checkbox(self):
        is_done = self._instance.is_done
        color = ft.Colors.GREY if is_done else None
        self._checkbox = ft.Checkbox(
            label=None,
            value=is_done,
            on_change=self.on_change_checkbox,
            fill_color=color,
        )

    def build_text(self):
        label = self.get_text_label()
        if not self._text:
            self._text = label
        else:
            self._text.controls = label.controls

    def build_expand_children_icon(self):
        has_children = self._instance.children.exists()

        if self.is_expanded:
            icon = ft.Icons.KEYBOARD_ARROW_DOWN
            tooltip = 'Скрыть вложенные задачи'
        else:
            icon = ft.Icons.KEYBOARD_ARROW_RIGHT
            tooltip = 'Показать вложенные задачи'

        if self._expand_children_icon:
            self._expand_children_icon.icon = icon
            self._expand_children_icon.tooltip = tooltip
            self._expand_children_icon.visible = has_children
        else:
            self._expand_children_icon = ft.IconButton(
                icon=icon,
                tooltip=tooltip,
                visible=has_children,
                on_click=self.on_click_expand_children_icon,
            )

    def on_click_expand_children_icon(self, e):
        if self.is_expanded:
            self._state['expanded'].discard(self._instance.id)
        else:
            self._state['expanded'].add(self._instance.id)

        self.build_expand_children_icon()

        show_children = self.is_expanded
        for control in self.parent.controls:
            control.visible = show_children or control == self

        self.parent.update()


    def get_text_label(self) -> ft.Row:
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
        self._edit_container = ToDoMutateContainer(self._state, self._instance)

    def on_change_checkbox(self, e):
        is_done = e.control.value
        self._instance.is_done = is_done
        self._instance.save(only=['is_done'])
        refresh_todo_list(self._state)

    def on_click_edit(self, e):
        for control in self.content.controls:
            is_edit_container = control == self._edit_container
            control.visible = is_edit_container

        self.update()

    def on_stop_editing(self):
        self._instance = ToDo.get(id=self._instance.id)

        for control in self.content.controls:
            if control == self._edit_container:
                control.visible = False
            elif control == self._expand_children_icon:
                control.visible = self._instance.children.exists()
            else:
                control.visible = True

        self.build_text()
        self.update()

    def on_click_add_children(self, e):
        children = ToDoMutateContainer(self._state, parent=self._instance)
        idx = None
        for i, control in enumerate(self.parent.controls):
            if control == self:
                idx = i + 1
                break

        self.parent.controls.insert(idx, children)
        self.parent.update()

    def on_click_remove(self, e):
        self._instance.delete_instance()
        refresh_todo_list(self._state)


class ToDoTabToDoViewControl(ft.Column):
    """
    Компонент отображения одного ТУДУ вместе с вложенными задачами
    """
    def __init__(self, instance: ToDo, state: TodoTabState, **kwargs):
        super().__init__(**kwargs)
        self._instance = instance
        self._state = state

        self._view_row: ft.Row | None = None

    def build(self):
        self._view_row = ToDoRowViewControl(self._instance, self._state)

        controls: list[Any] = [self._view_row]

        for children in self._instance.children:
            controls.append(ToDoRowViewControl(children, self._state))

        self.controls = controls
