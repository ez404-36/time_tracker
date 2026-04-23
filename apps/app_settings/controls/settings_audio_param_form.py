from dataclasses import dataclass
from pathlib import Path
import shutil

import flet as ft

from apps.app_settings.models import SettingsAudioParam
from apps.app_settings.utils import get_available_notification_sounds
from core.audio_player import AudioPlayer
from core.consts import USER_AUDIO_DIR
from core.di import container
from core.system_events.types import SystemEvent, SystemEventFileInfo
from ui.base.components.containers import BorderedContainer
from ui.base.components.text import TextComponent
from ui.consts import Icons


@dataclass(frozen=True)
class SettingsAudioParamFormData:
    disabled: bool
    sound: str | None
    volume_offset: int


class VolumeOffsetText(TextComponent):
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
        self._add_custom_sound_button: ft.IconButton | None = None
        self._file_picker: ft.FilePicker | None = None
        self._volume_offset_row: ft.Row | None = None
        self._volume_offset_text: VolumeOffsetText | None = None
        self._volume_offset_slider: ft.Slider | None = None

        self._audio_param = audio_param
        self._available_notification_sounds_map: dict[str, str] = self._get_notification_sounds_map()
        self._last_added_file: ft.FilePickerFile | None = None

        self._event_bus = container.event_bus

        self._event_bus.subscribe('media.add_file', self._on_add_file_event)
        self._event_bus.subscribe('media.delete_file', self._on_delete_file_event)

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
        self._sound_dropdown = self._create_notification_sound_dropdown()
        self._sound_play_button = ft.IconButton(
            icon=Icons.START,
            on_click=self._on_click_play_sound,
            visible=self._sound_dropdown.value is not None,
            tooltip='Воспроизвести звук',
        )

        self._file_picker = ft.FilePicker()

        self._add_custom_sound_button = ft.IconButton(
            icon=Icons.UPLOAD,
            on_click=self.on_click_add_custom_sound,
            tooltip='Добавить свой звук',
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
                self._add_custom_sound_button,
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
        if sound and (sound_path := self._available_notification_sounds_map.get(sound)):
            AudioPlayer.play(
                sound_path,
                volume_offset=self._volume_offset_slider.value,
            )

    async def on_click_add_custom_sound(self, e):
        added_files = await self._file_picker.pick_files(
            allow_multiple=False,
            file_type=ft.FilePickerFileType.AUDIO,
        )
        if not added_files:
            return

        self._last_added_file = added_files[0]

        filename = self._last_added_file.name
        path = self._last_added_file.path

        USER_AUDIO_DIR.mkdir(exist_ok=True, parents=True)
        shutil.copy(path, USER_AUDIO_DIR / filename)

        self._event_bus.publish(
            SystemEvent(
                type='media.add_file',
                data=SystemEventFileInfo(
                    filename=filename,
                    path=path,
                )
            )
        )

    def _on_change_volume_offset(self, e):
        value: ft.Number = e.control.value
        self._volume_offset_text.update_value(round(value, 1))

    def _on_change_switch(self, e):
        enabled = e.control.value
        self._sound_row.visible = enabled
        self._volume_offset_row.visible = enabled

        self.update()

    def _get_dropdown_options(self) -> list[ft.DropdownOption]:
        options: list[ft.DropdownOption] = []

        volume_offset_component = self._volume_offset_slider
        custom_audio_dir = str(USER_AUDIO_DIR)

        for file_name, sound_file_path in self._available_notification_sounds_map.items():
            def on_click_play_wrapper(_sound_path: Path | str):
                sound_path = _sound_path

                def _play(e):
                    AudioPlayer.play(
                        sound_path,
                        volume_offset=volume_offset_component.value,
                    )

                return _play


            controls = [
                ft.IconButton(
                    icon=Icons.PLAY_ARROW,
                    on_click=on_click_play_wrapper(sound_file_path),
                ),
                TextComponent(value=file_name)
            ]

            is_custom_uploaded_sound = sound_file_path.startswith(custom_audio_dir)
            if is_custom_uploaded_sound:
                def on_click_delete_wrapper(_sound_path: Path | str):
                    sound_path = Path(_sound_path)

                    def _delete(e):
                        sound_path.unlink(missing_ok=True)
                        self._event_bus.publish(
                            SystemEvent(
                                type='media.delete_file',
                                data=SystemEventFileInfo(
                                    filename=sound_path.name,
                                    path=sound_path,
                                )
                            )
                        )

                    return _delete

                controls.append(
                    ft.IconButton(
                        icon=Icons.DELETE,
                        tooltip='Удалить загруженный звук',
                        on_click=on_click_delete_wrapper(sound_file_path),
                    )
                )

            option = ft.DropdownOption(
                key=file_name,
                content=ft.Row(
                    controls=controls
                ),
            )
            options.append(option)

        return options

    def _on_change_sound_dropdown(self, e):
        has_value = e.control.value is not None

        self._sound_play_button.visible = has_value
        self._sound_play_button.update()

    def _on_add_file_event(self, data: SystemEventFileInfo):
        self._refresh_dropdown_options()
        if last_added_file := self._last_added_file:
            if last_added_file.path == data.path:
                self._sound_dropdown.value = data.filename
                self._sound_dropdown.update()

    def _on_delete_file_event(self, _data: SystemEventFileInfo):
        self._refresh_dropdown_options()

    def _refresh_dropdown_options(self):
        self._available_notification_sounds_map = self._get_notification_sounds_map()
        self._sound_dropdown.options = self._get_dropdown_options()
        self._sound_dropdown.update()

    def _create_notification_sound_dropdown(self) -> ft.Dropdown:
        return ft.Dropdown(
            label='Звук уведомления',
            menu_height=200,
            options=self._get_dropdown_options(),
            value=self._audio_param and self._audio_param.sound,
            on_select=self._on_change_sound_dropdown,
        )

    @staticmethod
    def _get_notification_sounds_map() -> dict[str, str]:
        available_notification_sounds = get_available_notification_sounds()
        return {
            Path(sound_file_path).name: sound_file_path
            for sound_file_path in available_notification_sounds
        }

