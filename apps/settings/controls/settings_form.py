from dataclasses import dataclass
from pathlib import Path

import flet as ft
import pytz
from playsound3 import playsound

from core.settings import AppSettings
from apps.settings.utils import get_available_notification_sounds
from core.consts import AUDIO_DIR
from ui.consts import Colors


@dataclass(frozen=True)
class SettingsFormData:
    idle_threshold: int
    enable_pomodoro: bool
    pomodoro_work_time: int | None
    pomodoro_rest_time: int | None
    enable_todo_deadline_sound_notifications: bool
    todo_deadline_sound: str | None
    enable_idle_start_sound_notifications: bool
    idle_start_sound: str | None
    client_timezone: str


class SettingsForm(ft.Container):
    """
    Форма изменения настроек
    """
    content: ft.ListView

    def __init__(self, app_settings: AppSettings, **kwargs):
        kwargs.update(
            dict(
                padding=10,
                border=ft.Border.all(1, Colors.GREY),
                border_radius=10,
                bgcolor=Colors.WHITE,
                width=500,
                height=400,
            )
        )

        super().__init__(**kwargs)
        self._app_settings = app_settings

        self._idle_threshold: ft.TextField | None = None

        self._enable_pomodoro_switch: ft.Switch | None = None
        self._pomodoro_work_time: ft.TextField | None = None
        self._pomodoro_rest_time: ft.TextField | None = None

        self._enable_todo_deadline_sound_switch: ft.Switch | None = None
        self._todo_deadline_sound_dropdown: ft.Dropdown | None = None

        self._enable_idle_start_sound_switch: ft.Switch | None = None
        self._idle_start_sound_dropdown: ft.Dropdown | None = None

        self._timezone_dropdown: ft.Dropdown | None = None

        self._available_notification_sounds = get_available_notification_sounds()

    def build(self):
        self._build_idle_threshold()
        self._build_enable_pomodoro_switch()
        self._build_pomodoro_work_time()
        self._build_pomodoro_rest_time()
        self._build_enable_todo_deadline_sound_switch()
        self._build_todo_deadline_sound_dropdown()
        self._build_enable_idle_start_sound_switch()
        self._build_idle_start_sound_dropdown()
        self._build_timezone_dropdown()

        content = ft.ListView(
            spacing=10,
            controls=[
                ft.Container(padding=6),
                self._idle_threshold,
                self._enable_pomodoro_switch,
                self._pomodoro_work_time,
                self._pomodoro_rest_time,
                ft.Divider(),
                self._enable_todo_deadline_sound_switch,
                self._todo_deadline_sound_dropdown,
                self._enable_idle_start_sound_switch,
                self._idle_start_sound_dropdown,
                ft.Divider(),
                self._timezone_dropdown,
            ]
        )
        self.content = content

    def collect_form_fields(self) -> SettingsFormData:
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

        return SettingsFormData(
            idle_threshold=idle_threshold,
            enable_pomodoro=self._enable_pomodoro_switch.value,
            pomodoro_work_time=pomodoro_work_time,
            pomodoro_rest_time=pomodoro_rest_time,
            enable_todo_deadline_sound_notifications=self._enable_todo_deadline_sound_switch.value,
            todo_deadline_sound=self._todo_deadline_sound_dropdown.value,
            enable_idle_start_sound_notifications=self._enable_idle_start_sound_switch.value,
            idle_start_sound=self._idle_start_sound_dropdown.value,
            client_timezone=self._timezone_dropdown.value,
        )

    def _build_idle_threshold(self):
        self._idle_threshold = ft.TextField(
            label='Порог бездействия (секунд)',
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

    def _build_enable_todo_deadline_sound_switch(self):
        self._enable_todo_deadline_sound_switch = ft.Switch(
            label='Включить звуковые уведомления для задач',
            value=self._app_settings.enable_todo_deadline_sound_notifications,
            on_change=self._on_change_todo_deadline_sound_switch,
        )

    def _on_change_todo_deadline_sound_switch(self, e):
        enabled = e.control.value
        self._todo_deadline_sound_dropdown.visible = enabled
        self.update()

    def _build_enable_idle_start_sound_switch(self):
        self._enable_idle_start_sound_switch = ft.Switch(
            label='Включить звуковые уведомления о начале бездействия',
            value=self._app_settings.enable_idle_start_sound_notifications,
            on_change=self._on_change_idle_start_sound_switch,
        )

    def _on_change_idle_start_sound_switch(self, e):
        enabled = e.control.value
        self._idle_start_sound_dropdown.visible = enabled
        self.update()

    def _build_todo_deadline_sound_dropdown(self):
        self._todo_deadline_sound_dropdown = self.get_notification_sound_dropdown()
        self._todo_deadline_sound_dropdown.visible = self._app_settings.enable_todo_deadline_sound_notifications
        self._todo_deadline_sound_dropdown.value = self._app_settings.todo_deadline_sound

    def _build_idle_start_sound_dropdown(self):
        self._idle_start_sound_dropdown = self.get_notification_sound_dropdown()
        self._idle_start_sound_dropdown.visible = self._app_settings.enable_idle_start_sound_notifications
        self._idle_start_sound_dropdown.value = self._app_settings.idle_start_sound

    def _build_timezone_dropdown(self):
        self._timezone_dropdown = ft.Dropdown(
            label='Часовой пояс',
            value=self._app_settings.client_timezone,
            menu_height=200,
            enable_filter=True,
            options=[
                ft.DropdownOption(
                    key=tz,
                )
                for tz in pytz.all_timezones
            ]
        )

    def get_notification_sound_dropdown(self) -> ft.Dropdown:
        options: list[ft.DropdownOption] = []

        for sound_file_path in self._available_notification_sounds:
            def on_click(e):
                sound_name = e.control.parent.controls[1].value
                playsound(AUDIO_DIR / sound_name)

            option = ft.DropdownOption(
                key=Path(sound_file_path).name,
                content=ft.Row(
                    controls=[
                        ft.IconButton(
                            icon=ft.Icons.PLAY_ARROW,
                            on_click=on_click,
                        ),
                        ft.Text(Path(sound_file_path).name)
                    ]
                ),
            )
            options.append(option)

        return ft.Dropdown(
            label='Звук уведомления',
            menu_height=200,
            options=options,
        )
