from typing import Self

import flet as ft

from core.controls.base_control import BaseControl
from core.state import State, ToDoTabControlsState


class TodoTabControl(BaseControl):
    def __init__(self, state: State):
        super().__init__(state)
        self._state: ToDoTabControlsState = state['tabs']['todo']['controls']

    @property
    def component(self) -> ft.Container:
        return self._state['tab']

    def build(self) -> Self:
        def todo_add_clicked(e):
            todo_list = self._state['list']

            def on_remove_click(e):
                todo_list.controls.remove(row)
                todo_list.update()

            row = ft.Row()
            checkbox = ft.Checkbox(label=self._state['input'].value)
            delete_icon = ft.IconButton(icon=ft.Icons.DELETE, on_click=on_remove_click)

            row.controls.extend([
                checkbox,
                delete_icon,
            ])

            todo_list.controls.append(row)
            self._state['input'].value = ""
            self._state['view'].update()

        self._state['input'] = ft.TextField(hint_text='Не забыть сделать')
        self._state['list'] = ft.Column()
        self._state['view'] = ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        self._state['input'],
                        ft.FloatingActionButton(
                            icon=ft.Icons.ADD,
                            on_click=todo_add_clicked,
                        ),
                    ]
                ),
                self._state['list'],
            ]
        )

        self._state['tab'] = ft.Container(
            padding=20,
            content=self._state['view'],
        )

        return self
