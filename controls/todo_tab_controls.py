from typing import Self

import flet as ft

from controls.base_control import BaseControl
from state import State, ToDoTabControlsState


class TodoTabControl(BaseControl):
    def __init__(self, state: State):
        super().__init__(state)
        self._state: ToDoTabControlsState = state['controls']['todo']

    @property
    def component(self) -> ft.Column:
        return self._state['todo_tab']

    def init(self) -> Self:
        def todo_add_clicked(e):
            self._state['todo_list'].controls.append(ft.Checkbox(label=self._state['todo_input'].value))
            self._state['todo_input'].value = ""
            self._state['todo_view'].update()

        self._state['todo_input'] = ft.TextField(hint_text='Не забыть сделать')
        self._state['todo_list'] = ft.Column()
        self._state['todo_view'] = ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        self._state['todo_input'],
                        ft.FloatingActionButton(
                            icon=ft.Icons.ADD,
                            on_click=todo_add_clicked,
                        ),
                    ]
                ),
                self._state['todo_list'],
            ]
        )

        self._state['todo_tab'] = ft.Column(
            controls=[
                ft.Row(controls=[ft.Text('TODO', size=30)]),
                self._state['todo_view'],
            ]
        )

        return self
