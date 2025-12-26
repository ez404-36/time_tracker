from typing import Optional

import flet as ft

from apps.time_tracker.helpers import ActivityTabHelpers, TimeTrackDBHelpers
from apps.time_tracker.models import Activity
from core.models import db
from core.state import ActivityTabState


class MutateActivityModalControl(ft.AlertDialog):
    """
    Модалка добавления/редактирования активности
    """

    def __init__(self, state: ActivityTabState, instance: Optional[Activity] = None, **kwargs):
        kwargs.setdefault('modal', True)
        kwargs.setdefault('adaptive', True)
        if instance:
            title = 'Редактировать активность'
        else:
            title = 'Добавить новую активность'
        kwargs.setdefault('title', title)
        super().__init__(**kwargs)
        self._state = state
        self._instance = instance

        self._title_input: ft.TextField | None = None
        self._pomodoro_checkbox: ft.Checkbox | None = None
        self._set_work_time_input: ft.TextField | None = None
        self._set_rest_time_input: ft.TextField | None = None
        self._submit: ft.TextButton | None = None

    def build(self):
        self._init_submit_button()
        self._init_activity_title_input()
        self._init_pomodoro_checkbox()
        self._init_set_work_time_input()
        self._init_set_rest_time_input()

        controls = self.get_controls()

        self.content = ft.Container(
            width=500,
            height=500,
            padding=10,
            content=ft.Column(
                controls=controls,
            ),
        )
        self.actions = [
            ft.TextButton('Отмена', on_click=lambda e: self.page.close(self)),
            self._submit,
        ]

    def _init_pomodoro_checkbox(self):
        self._pomodoro_checkbox = ft.Checkbox(
            label='Работаю с интервалами работы/отдыха',
            on_change=self._on_change_pomodoro_checkbox,
            value=getattr(self._instance, 'work_time', None) is not None,
        )

    def _on_change_pomodoro_checkbox(self, e):
        value = e.control.value

        for time_input in [
            self._set_work_time_input,
            self._set_rest_time_input,
        ]:
            time_input.visible = value

        self.update()

    def _init_submit_button(self):
        self._submit = ft.TextButton(
            "Сохранить",
            on_click=self._on_click_submit_button,
            disabled=not self._instance,
        )

    @db.atomic()
    def _on_click_submit_button(self, e):
        activity_title: str = self._title_input.value
        if self._pomodoro_checkbox.value:
            work_time = self._set_work_time_input.value
            rest_time = self._set_rest_time_input.value
        else:
            work_time = None
            rest_time = None

        if not self._instance:
            Activity.create(
                title=activity_title,
                work_time=work_time,
                rest_time=rest_time,
            )
            TimeTrackDBHelpers(self._state).refresh_activities()

        else:
            self._instance.title = activity_title
            self._instance.work_time = work_time
            self._instance.rest_time = rest_time
            self._instance.save(only=['title'])
            TimeTrackDBHelpers(self._state).refresh_activities()

        self._title_input.value = ''
        self._new_work_time = None
        self._new_rest_time = None

        activity_selector = self._state['controls']['view']['activity_selector']

        activity_selector.disabled = False
        activity_selector.tooltip = None
        activity_selector.label = 'Чем сегодня займемся?'
        ActivityTabHelpers(self._state).refresh_activity_selector_options()

        self.page.close(self)

    def _init_activity_title_input(self):
        self._title_input = ft.TextField(
            label='Чем планируешь заняться?',
            hint_text='Например, работа',
            on_change=self._on_change_activity_title_input,
            value=self._instance.title if self._instance else None,
        )

    def _on_change_activity_title_input(self, e):
        submit_button = self._submit

        submit_button.disabled = not e.control.value
        submit_button.update()

    def _init_set_work_time_input(self):
        current_work_time = getattr(self._instance, 'work_time', None)
        self._set_work_time_input = ft.TextField(
            label='Интервал работы (минут)',
            value=current_work_time,
            visible=current_work_time is not None,
        )

    def _init_set_rest_time_input(self):
        current_rest_time = getattr(self._instance, 'rest_time', None)
        self._set_rest_time_input = ft.TextField(
            label='Интервал отдыха (минут)',
            value=current_rest_time,
            visible=current_rest_time is not None,
        )

    def get_controls(self) -> list[ft.Control]:
        return [
            self._title_input,
            ft.Divider(),
            self._pomodoro_checkbox,
            ft.Container(padding=6),
            self._set_work_time_input,
            self._set_rest_time_input,
        ]
