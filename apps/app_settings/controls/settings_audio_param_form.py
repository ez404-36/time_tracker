from dataclasses import dataclass
from pathlib import Path

import flet as ft

from apps.app_settings.models import SettingsAudioParam
from apps.app_settings.utils import get_available_notification_sounds
from core.audio_player import AudioPlayer
from core.consts import AUDIO_DIR
from ui.base.components.containers import BorderedContainer
from ui.consts import Icons


@dataclass(frozen=True)
class SettingsAudioParamFormData:
    disabled: bool
    sound: str | None
    volume_offset: int


class SettingsAudioParamForm(BorderedContainer):
    content: ft.ListView

    def __init__(self, audio_param: SettingsAudioParam | None, **kwargs):
        kwargs['padding'] = 10
        super().__init__(**kwargs)

        self._enable_switch: ft.Switch | None = None
        self._sound_dropdown: ft.Dropdown | None = None
        self._volume_offset_row: ft.Row | None = None
        self._volume_offset_slider: ft.Slider | None = None

        self._audio_param = audio_param
        self._available_notification_sounds = get_available_notification_sounds()

    def build(self):
        self._enable_switch = ft.Switch(
            label='Включить/Выключить',
            value=not self._audio_param.disabled if self._audio_param else False,
            on_change=self._on_change_switch,
        )
        self._volume_offset_slider = ft.Slider(
            label='Усиление/Уменьшение громкости, в децибелах',
            min=-20,
            max=20,
            width=200,
            value=self._audio_param.volume_offset if self._audio_param else 0,
        )
        self._sound_dropdown = self.get_notification_sound_dropdown()

        self._volume_offset_row = ft.Row(
            width=300,
            visible=not self._audio_param.disabled if self._audio_param else False,
            controls=[
                ft.Text('Усиление/Уменьшение громкости, Дб'),
                self._volume_offset_slider,
            ]
        )

        self.content = ft.ListView(
            spacing=10,
            controls=[
                self._enable_switch,
                self._sound_dropdown,
                self._volume_offset_row,
            ]
        )

    def collect_form_fields(self) -> SettingsAudioParamFormData:
        return SettingsAudioParamFormData(
            disabled=not self._enable_switch.value,
            sound=self._sound_dropdown.value,
            volume_offset=self._volume_offset_slider.value,
        )

    def _on_change_switch(self, e):
        enabled = e.control.value
        self._sound_dropdown.visible = enabled
        self._volume_offset_row.visible = enabled

        self.update()

    def get_notification_sound_dropdown(self) -> ft.Dropdown:
        options: list[ft.DropdownOption] = []

        volume_offset_component = self._volume_offset_slider

        for sound_file_path in self._available_notification_sounds:
            def on_click(e):
                sound_name: str = e.control.parent.controls[1].value
                # _self: SettingsAudioParamForm = e.control.parent.parent.parent.parent.parent
                AudioPlayer.play(
                    AUDIO_DIR / sound_name,
                    volume_offset=volume_offset_component.value,
                )

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
            visible=not self._audio_param.disabled if self._audio_param else False,
        )
