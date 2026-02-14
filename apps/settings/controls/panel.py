from typing import TypedDict

import flet as ft

from apps.settings.models import AppSettings


class SettingsForm(TypedDict):
    idle_threshold: int
    enable_pomodoro: bool
    pomodoro_work_time: int | None
    pomodoro_rest_time: int | None


class SettingsPanel(ft.Container):
    """
    Панель настроек
    """

    def __init__(self, app_settings: AppSettings, **kwargs):
        kwargs.update(
            dict(
                padding=10,
                border=ft.border.all(1, "grey"),
                border_radius=10,
                bgcolor=ft.Colors.WHITE,
                width=400,
                height=400,
            )
        )

        super().__init__(**kwargs)
        self._app_settings = app_settings

        self._idle_threshold: ft.TextField | None = None
        self._enable_pomodoro_switch: ft.Switch | None = None
        self._pomodoro_work_time: ft.TextField | None = None
        self._pomodoro_rest_time: ft.TextField | None = None

    def build(self):
        self._build_idle_threshold()
        self._build_enable_pomodoro_switch()
        self._build_pomodoro_work_time()
        self._build_pomodoro_rest_time()

        content = ft.Column(
            spacing=10,
            scroll=ft.ScrollMode.AUTO,
            controls=[
                self._idle_threshold,
                self._enable_pomodoro_switch,
                self._pomodoro_work_time,
                self._pomodoro_rest_time,
                ft.Switch(
                    label='Включить звуковые уведомления для задач',
                    value=self._app_settings.enable_todo_sound_deadline_notifications,
                ),
                ft.Switch(
                    label='Включить звуковые уведомления о начала бездействия',
                    value=self._app_settings.enable_idle_start_sound_notifications,
                ),
            ]
        )
        self.content = content

    def collect_form_fields(self) -> SettingsForm:
        idle_threshold = self._idle_threshold.value
        if idle_threshold:
            idle_threshold = int(idle_threshold)
        else:
            idle_threshold = 0

        pomodoro_work_time = self._pomodoro_work_time.value
        if pomodoro_work_time:
            pomodoro_work_time = int(pomodoro_work_time)
        else:
            pomodoro_work_time = None

        pomodoro_rest_time = self._pomodoro_rest_time.value
        if pomodoro_rest_time:
            pomodoro_rest_time = int(pomodoro_rest_time)
        else:
            pomodoro_rest_time = None

        return SettingsForm(
            idle_threshold=idle_threshold,
            enable_pomodoro=self._enable_pomodoro_switch.value,
            pomodoro_work_time=pomodoro_work_time,
            pomodoro_rest_time=pomodoro_rest_time,
        )

    def _build_idle_threshold(self):
        self._idle_threshold = ft.TextField(
            label='Порог бездействия (секунд)',
            helper_text='0 - отключает определение времени бездействия',
            value=self._app_settings.idle_threshold,
            input_filter=ft.NumbersOnlyInputFilter()
        )

    def _build_enable_pomodoro_switch(self):
        self._enable_pomodoro_switch = ft.Switch(
            label='Включить работу по таймеру',
            value=self._app_settings.enable_pomodoro,
            on_change=self._on_change_enable_pomodoro_switch,
        )

    def _on_change_enable_pomodoro_switch(self, e):
        value = e.control.value

        self._pomodoro_work_time.visible = value
        self._pomodoro_rest_time.visible = value

        self.update()

    def _build_pomodoro_work_time(self):
        self._pomodoro_work_time = ft.TextField(
            label='Время непрерывной работы (минут)',
            value=self._app_settings.pomodoro_work_time,
            visible=self._app_settings.enable_pomodoro,
        )

    def _build_pomodoro_rest_time(self):
        self._pomodoro_rest_time = ft.TextField(
            label='Время отдыха (минут)',
            value=self._app_settings.pomodoro_rest_time,
            visible=self._app_settings.enable_pomodoro,
        )
