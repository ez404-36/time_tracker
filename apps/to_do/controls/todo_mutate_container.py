import datetime
from typing import Optional

import flet as ft
from flet.core.border import Border, BorderSide

from apps.to_do.models import ToDo


class ToDoMutateContainer(ft.Container):
    """
    Контейнер создания/изменения объекта ТУДУ
    """

    def __init__(self, instance: Optional[ToDo] = None, **kwargs):
        bs = BorderSide(2, color=ft.Colors.BLUE)
        border = Border(left=bs, top=bs, right=bs, bottom=bs)

        kwargs.setdefault('padding', 10)
        kwargs.setdefault('visible', False)
        kwargs.setdefault('border', border)
        super().__init__(**kwargs)

        self._instance = instance
        self._new_deadline_date: datetime.date | None = None
        self._new_deadline_time: datetime.time | None = None

        self._edit_field: ft.TextField | None = None
        self._edit_date_button: ft.TextButton | None = None
        self._edit_time_button: ft.TextButton | None = None
        self._submit_icon: ft.IconButton | None = None

    def build(self):
        self._build_edit_field()
        self._build_edit_date_button()
        self._build_edit_time_button()
        self._build_submit_button()

        self.content = ft.Row(
            controls=[
                self._edit_field,
                ft.Column(
                    controls=[
                        self._edit_date_button,
                        self._edit_time_button,
                    ]
                ),
                self._submit_icon,
            ]
        )

    def _build_edit_field(self):
        self._edit_field = ft.TextField(value=self._instance.title)

    def _build_edit_date_button(self):
        deadline_date = self._instance.deadline_date

        self._edit_date_button = ft.TextButton(
            f'Дата: ({self._instance.deadline_date_str or "Не выбрана"})',
            on_click=lambda e: self.page.open(
                ft.DatePicker(
                    first_date=datetime.datetime.now().date(),
                    value=deadline_date,
                    on_change=self._on_change_deadline_date,
                )
            )
        )

    def _on_change_deadline_date(self, e):
        value: datetime.date = e.control.value.date()
        self._new_deadline_date = value
        self._edit_date_button.text = f'Дата: ({value.strftime("%d.%m.%Y")})'
        self._edit_date_button.update()

    def _build_edit_time_button(self):
        deadline_time = self._instance.deadline_time

        self._edit_time_button = ft.TextButton(
            f'Время: ({self._instance.deadline_time_str or "Не выбрано"})',
            on_click=lambda e: self.page.open(
                ft.TimePicker(
                    value=deadline_time or datetime.datetime.now().time(),
                    on_change=self._on_change_deadline_time,
                )
            )
        )

    def _on_change_deadline_time(self, e):
        value = e.control.value
        self._new_deadline_time = value
        self._edit_time_button.text = f'Время: ({value.strftime('%H:%M')})'
        self._edit_time_button.update()

    def _build_submit_button(self):
        self._submit_icon = ft.IconButton(
            icon=ft.Icons.CHECK,
            on_click=self._on_click_submit,
            tooltip='Сохранить',
        )

    def _on_click_submit(self, e):
        value = self._edit_field.value
        deadline_date = self._new_deadline_date
        deadline_time = self._new_deadline_time

        self._instance.title = value
        if deadline_date:
            self._instance.deadline_date = deadline_date
        if deadline_time:
            self._instance.deadline_time = deadline_time
        self._instance.save()

        self._new_deadline_date = None
        self._new_deadline_time = None

        self.parent.on_stop_editing()
