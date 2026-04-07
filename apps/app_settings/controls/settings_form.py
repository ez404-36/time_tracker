from dataclasses import dataclass
from pathlib import Path

import flet as ft
import pytz
from playsound3 import playsound

from apps.app_settings.controls.types import SettingsFormMode
from apps.app_settings.utils import get_available_notification_sounds
from core.consts import AUDIO_DIR
from core.di import container
from ui.base.components.containers import BorderedContainer
from ui.consts import Icons


@dataclass(frozen=True)
class SettingsTrackerFormData:
    enable_window_tracking: bool
    enable_idle_tracking: bool
    idle_threshold: int
    enable_pomodoro: bool
    pomodoro_work_time: int # минут
    pomodoro_rest_time: int # минут


@dataclass(frozen=True)
class SettingsAudioFormData:
    enable_task_deadline_sound_notifications: bool
    task_deadline_sound: str | None
    enable_idle_start_sound_notifications: bool
    idle_start_sound: str | None

@dataclass(frozen=True)
class SettingsCommonFormData:
    client_timezone: str


@dataclass(frozen=True)
class SettingsFormData:
    common: SettingsCommonFormData | None = None
    audio: SettingsAudioFormData | None = None
    tracker: SettingsTrackerFormData | None = None


class SettingsForm(BorderedContainer):
    """
    Форма изменения настроек
    """
    content: ft.ListView

    def __init__(
            self,
            mode: SettingsFormMode,
            in_modal: bool,
            **kwargs,
    ):
        if in_modal:
            kwargs.setdefault('width', 400)

        super().__init__(**kwargs)
        self._mode = mode
        self._app_settings = container.app_settings

        self._enable_window_tracking_switch: ft.Switch | None = None

        self._enable_idle_tracking_switch: ft.Switch | None = None
        self._idle_threshold: ft.TextField | None = None

        self._enable_pomodoro_switch: ft.Switch | None = None
        self._pomodoro_work_time: ft.TextField | None = None
        self._pomodoro_rest_time: ft.TextField | None = None

        self._enable_task_deadline_sound_switch: ft.Switch | None = None
        self._task_deadline_sound_dropdown: ft.Dropdown | None = None

        self._enable_idle_start_sound_switch: ft.Switch | None = None
        self._idle_start_sound_dropdown: ft.Dropdown | None = None

        self._timezone_dropdown: ft.Dropdown | None = None

        self._available_notification_sounds = get_available_notification_sounds()

    def build(self):
        self._build_enable_window_tracking_switch()
        self._build_enable_idle_tracking_switch()
        self._build_idle_threshold()
        self._build_enable_pomodoro_switch()
        self._build_pomodoro_work_time()
        self._build_pomodoro_rest_time()
        self._build_enable_task_deadline_sound_switch()
        self._build_task_deadline_sound_dropdown()
        self._build_enable_idle_start_sound_switch()
        self._build_idle_start_sound_dropdown()
        self._build_timezone_dropdown()

        if self._mode == 'tracker':
            controls = [
                ft.Container(padding=6),
                self._enable_window_tracking_switch,
                self._enable_idle_tracking_switch,
                self._idle_threshold,
                self._enable_pomodoro_switch,
                self._pomodoro_work_time,
                self._pomodoro_rest_time,
            ]
        else:
            controls = [
                ft.Container(padding=6),
                ft.Text(value='Общие настройки'),
                self._timezone_dropdown,
                ft.Divider(),
                ft.Text(value='Настройки трекера'),
                self._enable_window_tracking_switch,
                self._enable_idle_tracking_switch,
                self._idle_threshold,
                self._enable_pomodoro_switch,
                self._pomodoro_work_time,
                self._pomodoro_rest_time,
                ft.Divider(),
                ft.Text(value='Настройки звука'),
                self._enable_task_deadline_sound_switch,
                self._task_deadline_sound_dropdown,
                self._enable_idle_start_sound_switch,
                self._idle_start_sound_dropdown,
            ]

        content = ft.ListView(
            spacing=10,
            controls=controls
        )
        self.content = content

    def collect_form_fields(self) -> SettingsFormData:
        tracker_settings = self._collect_tracker_settings()

        if self._mode == 'tracker':
            audio_settings = None
            common_settings = None
        else:
            audio_settings = self._collect_audio_settings()
            common_settings = self._collect_common_settings()

        return SettingsFormData(
            common=common_settings,
            tracker=tracker_settings,
            audio=audio_settings,
        )

    def _collect_common_settings(self) -> SettingsCommonFormData:
        return SettingsCommonFormData(
            client_timezone=self._timezone_dropdown.value,
        )

    def _collect_audio_settings(self) -> SettingsAudioFormData:
        return SettingsAudioFormData(
            enable_task_deadline_sound_notifications=self._enable_task_deadline_sound_switch.value,
            task_deadline_sound=self._task_deadline_sound_dropdown.value,
            enable_idle_start_sound_notifications=self._enable_idle_start_sound_switch.value,
            idle_start_sound=self._idle_start_sound_dropdown.value,
        )

    def _collect_tracker_settings(self) -> SettingsTrackerFormData:
        enable_idle_tracking = self._enable_idle_tracking_switch.value
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

        return SettingsTrackerFormData(
            enable_window_tracking=self._enable_window_tracking_switch.value,
            enable_idle_tracking=enable_idle_tracking,
            idle_threshold=idle_threshold,
            enable_pomodoro=self._enable_pomodoro_switch.value,
            pomodoro_work_time=pomodoro_work_time,
            pomodoro_rest_time=pomodoro_rest_time,
        )

    def _build_enable_window_tracking_switch(self):
        self._enable_window_tracking_switch = ft.Switch(
            label='Отслеживание окон',
            value=self._app_settings.enable_window_tracking,
        )

    def _build_enable_idle_tracking_switch(self):
        self._enable_idle_tracking_switch = ft.Switch(
            label='Отслеживание бездействия',
            value=self._app_settings.enable_idle_tracking,
            on_change=self._on_change_enable_idle_tracking_switch,
        )

    def _on_change_enable_idle_tracking_switch(self, e):
        value = e.control.value

        self._idle_threshold.visible = value
        self.update()


    def _build_idle_threshold(self):
        self._idle_threshold = ft.TextField(
            label='Порог бездействия (секунд)',
            value=self._app_settings.idle_threshold,
            input_filter=ft.NumbersOnlyInputFilter(),
            visible=self._app_settings.enable_idle_tracking,
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

    def _build_enable_task_deadline_sound_switch(self):
        self._enable_task_deadline_sound_switch = ft.Switch(
            label='Звуковые уведомления для задач',
            value=self._app_settings.enable_task_deadline_sound_notifications,
            on_change=self._on_change_task_deadline_sound_switch,
        )

    def _on_change_task_deadline_sound_switch(self, e):
        enabled = e.control.value
        self._task_deadline_sound_dropdown.visible = enabled
        self.update()

    def _build_enable_idle_start_sound_switch(self):
        self._enable_idle_start_sound_switch = ft.Switch(
            label='Звуковые уведомления о начале бездействия',
            value=self._app_settings.enable_idle_start_sound_notifications,
            on_change=self._on_change_idle_start_sound_switch,
        )

    def _on_change_idle_start_sound_switch(self, e):
        enabled = e.control.value
        self._idle_start_sound_dropdown.visible = enabled
        self.update()

    def _build_task_deadline_sound_dropdown(self):
        self._task_deadline_sound_dropdown = self.get_notification_sound_dropdown()
        self._task_deadline_sound_dropdown.visible = self._app_settings.enable_task_deadline_sound_notifications
        self._task_deadline_sound_dropdown.value = self._app_settings.task_deadline_sound

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
                            icon=Icons.PLAY_ARROW,
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
