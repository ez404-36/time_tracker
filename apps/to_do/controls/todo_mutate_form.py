import datetime
from dataclasses import dataclass
from typing import Collection

import flet as ft

from apps.to_do.models import ToDo
from core.utils import to_current_tz


@dataclass
class ToDoFormData:
    title: str
    description: str | None
    parent_id: int | None
    deadline_date: datetime.date | None
    deadline_time: datetime.time | None


class TodoMutateForm(ft.Container):
    """
    Форма создания/редактирования задачи
    """

    content: ft.ListView

    def __init__(
        self,
        instance: ToDo | None = None,
        parent_instance: ToDo | None = None,
        **kwargs
    ):
        kwargs.update(
            dict(
                padding=10,
                width=500,
                height=400,
            )
        )

        super().__init__(**kwargs)
        self._instance = instance
        self._parent_instance = parent_instance

        self._new_deadline_date: datetime.date | None = None
        self._new_deadline_time: datetime.time | None = None

        self._title_field: ft.TextField | None = None
        self._description_field: ft.TextField | None = None
        self._parent_dropdown: ft.Dropdown | None = None
        self._edit_date_button: ft.TextButton | None = None
        self._date_picker: ft.DatePicker | None = None
        self._edit_time_button: ft.TextButton | None = None
        self._time_picker: ft.TimePicker | None = None

    def build(self):
        self._build_title_field()
        self._build_description_field()
        self._build_parent_dropdown()
        self._build_date_picker()
        self._build_time_picker()
        self._build_edit_date_button()
        self._build_edit_time_button()

        self.content = ft.ListView(
            spacing=10,
            controls=[
                self._title_field,
                self._description_field,
                self._parent_dropdown,
                self._edit_date_button,
                self._edit_time_button,
            ]
        )

    def collect_form_fields(self) -> ToDoFormData:
        parent_id = self._parent_dropdown.value

        return ToDoFormData(
            title=self._title_field.value,
            description=self._description_field.value,
            parent_id=parent_id and int(parent_id),
            deadline_date=self._new_deadline_date,
            deadline_time=self._new_deadline_time,
        )

    def _build_title_field(self):
        self._title_field = ft.TextField(
            hint_text='Название задачи',
        )

    def _build_description_field(self):
        self._description_field = ft.TextField(
            hint_text='Описание задачи',
            multiline=True,
            shift_enter=True,
        )

    def _build_parent_dropdown(self):
        root_todos = self._get_root_todos()

        if self._instance:
            value = self._instance.parent_id and str(self._instance.parent.id)
        elif self._parent_instance:
            value = str(self._parent_instance.id)
        else:
            value = None

        self._parent_dropdown = ft.Dropdown(
            text='Связать с задачей',
            value=value,
            options=[
                ft.DropdownOption(
                    key=str(root_todo.id),
                    text=str(root_todo)
                )
                for root_todo in root_todos
            ],
            visible=len(root_todos) > 0,
            disabled=self._parent_instance is not None,
        )

    @staticmethod
    def _get_root_todos() -> Collection[ToDo]:
        return ToDo().select().where(ToDo.parent == None)

    def _build_edit_date_button(self):
        selected_date = getattr(self._instance, 'deadline_date_str', None) or "Не выбрана"
        button_label = f'Дата: ({selected_date})'

        self._edit_date_button = ft.TextButton(
            content=button_label,
            on_click=self._on_click_date_button,
        )

    def _on_click_date_button(self, e):
        if not self._date_picker.open:
            self.page.show_dialog(
                self._date_picker
            )

    def _build_date_picker(self):
        self._date_picker = ft.DatePicker(
            first_date=datetime.datetime.now().date(),
            current_date=datetime.datetime.now().date(),
            value=getattr(self._instance, 'deadline_date', None),
            on_change=self._on_change_deadline_date,
        )

    def _on_change_deadline_date(self, e):
        value: datetime.date = to_current_tz(e.control.value).date()
        self._new_deadline_date = value
        if edit_date_button := self._edit_date_button:
            edit_date_button.content = f'Дата: ({value.strftime("%d.%m.%Y")})'
            edit_date_button.update()

    def _build_edit_time_button(self):
        selected_time = getattr(self._instance, 'deadline_time_str', None) or "Не выбрано"
        button_label = f'Время: ({selected_time})'

        self._edit_time_button = ft.TextButton(
            content=button_label,
            on_click=self._on_click_edit_time_button,
        )

    def _on_click_edit_time_button(self, e):
        if not self._time_picker.open:
            self.page.show_dialog(self._time_picker)

    def _build_time_picker(self):
        self._time_picker = ft.TimePicker(
            value=getattr(self._instance, 'deadline_time', None) or datetime.datetime.now().time(),
            on_change=self._on_change_deadline_time,
        )

    def _on_change_deadline_time(self, e):
        value = e.control.value
        self._new_deadline_time = value
        if edit_time_button := self._edit_time_button:
            edit_time_button.content = f'Время: ({value.strftime('%H:%M')})'
            edit_time_button.update()