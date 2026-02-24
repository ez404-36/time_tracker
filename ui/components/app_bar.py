import flet as ft

from apps.settings.controls.modal import SettingsModal
from ui.consts import Icons


class AppBar(ft.AppBar):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def build(self):
        self.leading = ft.IconButton(
            icon=Icons.MENU,
            on_click=self._on_click_menu,
        )
        self.bgcolor = ft.Colors.with_opacity(0.04, ft.CupertinoColors.SYSTEM_BACKGROUND)

        self.actions = [
            ft.IconButton(
                icon=Icons.SETTINGS,
                tooltip='Настройки',
                on_click=lambda e: self.page.show_dialog(SettingsModal()),
            )
        ]

    async def _on_click_menu(self):
        await self.page.show_drawer()

