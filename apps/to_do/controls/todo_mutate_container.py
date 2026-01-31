import datetime
from typing import Optional

import flet as ft
from flet import Padding, BorderSide, Border, Control

from apps.to_do.helpers import refresh_todo_list
from apps.to_do.models import ToDo
from core.state import TodoTabState


class ToDoMutateContainer(ft.Container):
    """
    Контейнер создания/изменения объекта ТУДУ
    """
    parent: ft.Row
    content: ft.Row | ft.Column
    page: ft.Page

    def __init__(
            self,
            state: TodoTabState,
            instance: Optional[ToDo] = None,
            parent_todo: Optional[ToDo] = None,
            **kwargs
    ):

        if not parent_todo:
            padding = Padding(left=10, top=10, right=10, bottom=10)
        else:
            padding = Padding(left=60, top=10, right=10, bottom=10)

        kwargs.setdefault('padding', padding)

        if instance or parent_todo:
            bs = BorderSide(2, color=ft.Colors.BLUE)
            border = Border(left=bs, top=bs, right=bs, bottom=bs)
            kwargs.setdefault('visible', parent_todo is not None)
            kwargs.setdefault('border', border)

        super().__init__(**kwargs)

        self._instance = instance
        self._parent_todo = parent_todo
        self._state = state
        self._new_deadline_date: datetime.date | None = None
        self._new_deadline_time: datetime.time | None = None

        self._title_field: ft.TextField | None = None
        self._edit_date_button: ft.TextButton | None = None
        self._edit_time_button: ft.TextButton | None = None
        self._submit_button: ft.IconButton | ft.TextButton | None = None
        self._cancel_button: ft.IconButton | None = None

    def build(self):
        self._build_title_field()
        self._build_edit_date_button()
        self._build_edit_time_button()
        self._build_submit_button()
        self._build_cancel_button()

        if self._instance or self._parent_todo:
            controls: list[Control] = [
                self._title_field,
                ft.Column(
                    controls=[
                        self._edit_date_button,
                        self._edit_time_button,
                    ]
                ),
                self._submit_button,
                self._cancel_button,
            ]

            self.content = ft.Row(
                controls=controls
            )
        else:
            self.content = ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            self._title_field,
                            self._submit_button,
                        ]
                    ),
                    ft.Row(
                        controls=[
                            self._edit_date_button,
                            self._edit_time_button,
                        ]
                    ),
                ]
            )

    def _build_title_field(self):
        if self._instance:
            self._title_field = ft.TextField(value=self._instance.title)
        else:
            def on_change(e):
                value = e.control.value
                has_value = bool(value)
                self._submit_button.disabled = not has_value
                self._edit_date_button.visible = has_value
                self._edit_time_button.visible = has_value

                self.parent.update()

            self._title_field = ft.TextField(
                hint_text='Не забыть сделать',
                on_change=on_change
            )

    def _build_edit_date_button(self):
        self._edit_date_button = ft.TextButton(
            f'Дата: ({getattr(self._instance, 'deadline_date_str', None) or "Не выбрана"})',
            on_click=lambda e: self.page.open(
                ft.DatePicker(
                    first_date=datetime.datetime.now().date(),
                    current_date=datetime.datetime.now().date(),
                    value=getattr(self._instance, 'deadline_date', None),
                    on_change=self._on_change_deadline_date,
                )
            ),
            visible=self._instance is not None or self._parent_todo is not None,
        )

    def _on_change_deadline_date(self, e):
        value: datetime.date = e.control.value.date()
        self._new_deadline_date = value
        if edit_date_button := self._edit_date_button:
            edit_date_button.content = f'Дата: ({value.strftime("%d.%m.%Y")})'
            edit_date_button.update()

    def _build_edit_time_button(self):
        self._edit_time_button = ft.TextButton(
            f'Время: ({getattr(self._instance, 'deadline_time_str', None) or "Не выбрано"})',
            on_click=lambda e: self.page.open(
                ft.TimePicker(
                    value=getattr(self._instance, 'deadline_time', None) or datetime.datetime.now().time(),
                    on_change=self._on_change_deadline_time,
                )
            ),
            visible=self._instance is not None or self._parent_todo is not None,
        )

    def _on_change_deadline_time(self, e):
        value = e.control.value
        self._new_deadline_time = value
        if edit_time_button := self._edit_time_button:
            edit_time_button.content = f'Время: ({value.strftime('%H:%M')})'
            edit_time_button.update()

    def _build_submit_button(self):
        if self._instance:
            self._submit_button = ft.IconButton(
                icon=ft.Icons.CHECK,
                on_click=self._on_click_submit,
                tooltip='Сохранить',
            )
        else:
            def on_click(e):
                value = self._title_field and self._title_field.value
                ToDo.create(
                    title=value,
                    deadline_date=self._new_deadline_date,
                    deadline_time=self._new_deadline_time,
                    parent=self._parent_todo,
                )
                refresh_todo_list(self._state)

                if not self._parent_todo:
                    self._title_field.value = ''
                    self._submit_button.disabled = True
                    self._edit_date_button.visible = False
                    self._edit_time_button.visible = False
                    self.update()
                elif self.parent:
                    self.parent.controls.remove(self)
                    self.parent.update()

            self._submit_button = ft.TextButton(
                text='Добавить',
                disabled=True,
                on_click=on_click
            )

    def _build_cancel_button(self):
        visible = self._instance is not None or self._parent_todo is not None
        self._cancel_button = ft.IconButton(
            icon=ft.Icons.CANCEL,
            icon_color=ft.Colors.RED_300,
            visible=visible,
            tooltip='Отменить',
            on_click=self._on_click_cancel,
        )

    def _on_click_cancel(self, e):
        parent = self.parent
        if hasattr(parent, 'parent'):
            parent = parent.parent

        if hasattr(parent, 'on_stop_editing'):
            parent.on_stop_editing()
        else:
            self.parent.controls.remove(self)
            self.parent.update()

    def _on_click_submit(self, e):
        value = self._title_field and self._title_field.value
        deadline_date = self._new_deadline_date
        deadline_time = self._new_deadline_time

        if self._instance:
            self._instance.title = value
            if deadline_date:
                self._instance.deadline_date = deadline_date
            if deadline_time:
                self._instance.deadline_time = deadline_time
            self._instance.save()

            self._new_deadline_date = None
            self._new_deadline_time = None

            parent = getattr(self.parent, 'parent', None)
            if parent and hasattr(parent, 'on_stop_editing'):
                parent.on_stop_editing()
