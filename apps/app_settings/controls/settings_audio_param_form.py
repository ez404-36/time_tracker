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


class VolumeOffsetText(ft.Text):
    def __init__(self, volume_offset: ft.Number, **kwargs):
        super().__init__(**kwargs)
        self.volume_offset = volume_offset

    def build(self):
        self.value = self._get_value()

    def update_value(self, volume_offset: ft.Number):
        self.volume_offset = volume_offset
        self.value = self._get_value()
        self.update()

    def _get_value(self) -> str:
        return f'Усиление/Уменьшение громкости: {self.volume_offset} Дб'


class SettingsAudioParamForm(BorderedContainer):
    content: ft.ListView

    def __init__(self, audio_param: SettingsAudioParam | None, **kwargs):
        kwargs['padding'] = 10
        super().__init__(**kwargs)

        self._enable_switch: ft.Switch | None = None
        self._sound_row: ft.Row | None = None
        self._sound_dropdown: ft.Dropdown | None = None
        self._sound_play_button: ft.IconButton | None = None
        self._volume_offset_row: ft.Row | None = None
        self._volume_offset_text: VolumeOffsetText | None = None
        self._volume_offset_slider: ft.Slider | None = None

        self._audio_param = audio_param
        self._available_notification_sounds = get_available_notification_sounds()

    def build(self):
        self._enable_switch = ft.Switch(
            label='Включить/Выключить',
            value=not self._audio_param.disabled if self._audio_param else False,
            on_change=self._on_change_switch,
        )
        self._volume_offset_text = VolumeOffsetText(
            volume_offset=float(self._audio_param.volume_offset) if self._audio_param else 0,
        )
        self._volume_offset_slider = ft.Slider(
            min=-20.0,
            max=20.0,
            width=400,
            value=float(self._audio_param.volume_offset) if self._audio_param else 0,
            on_change_end=self._on_change_volume_offset,
        )
        self._sound_dropdown = self.get_notification_sound_dropdown()
        self._sound_play_button = ft.IconButton(
            icon=Icons.START,
            on_click=self._on_click_play_sound,
            visible=self._sound_dropdown.value is not None,
            tooltip='Воспроизвести звук',
        )

        self._volume_offset_row = ft.Row(
            width=300,
            visible=not self._audio_param.disabled if self._audio_param else False,
            controls=[
                self._volume_offset_text,
                self._volume_offset_slider,
            ]
        )

        self._sound_row = ft.Row(
            width=300,
            visible=not self._audio_param.disabled if self._audio_param else False,
            controls=[
                self._sound_dropdown,
                self._sound_play_button,
            ]
        )

        self.content = ft.ListView(
            spacing=10,
            controls=[
                self._enable_switch,
                self._sound_row,
                self._volume_offset_row,
            ]
        )

    def collect_form_fields(self) -> SettingsAudioParamFormData:
        return SettingsAudioParamFormData(
            disabled=not self._enable_switch.value,
            sound=self._sound_dropdown.value,
            volume_offset=round(self._volume_offset_slider.value, 1),
        )

    def _on_click_play_sound(self, e):
        sound = self._sound_dropdown.value
        if self._sound_dropdown.value:
            AudioPlayer.play(
                AUDIO_DIR / sound,
                volume_offset=self._volume_offset_slider.value,
            )

    def _on_change_volume_offset(self, e):
        value: ft.Number = e.control.value
        self._volume_offset_text.update_value(round(value, 1))

    def _on_change_switch(self, e):
        enabled = e.control.value
        self._sound_row.visible = enabled
        self._volume_offset_row.visible = enabled

        self.update()

    def get_notification_sound_dropdown(self) -> ft.Dropdown:
        options: list[ft.DropdownOption] = []

        volume_offset_component = self._volume_offset_slider

        for sound_file_path in self._available_notification_sounds:
            def on_click(e):
                sound_name: str = e.control.parent.controls[1].value
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
            value=self._audio_param and self._audio_param.sound,
            on_select=self._on_change_sound_dropdown,
        )

    def _on_change_sound_dropdown(self, e):
        has_value = e.control.value is not None

        self._sound_play_button.visible = has_value
        self._sound_play_button.update()
