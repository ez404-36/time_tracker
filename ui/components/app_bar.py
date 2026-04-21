import subprocess

import flet as ft

from apps.notifications.services.notification_sender import NotificationSender
from core.settings import IS_FFMPEG_INSTALLED, PLATFORM, USE_X11
from ui.consts import Colors, Icons


class AppBar(ft.AppBar):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def build(self):
        self.leading = ft.IconButton(
            icon=Icons.MENU,
            on_click=self._on_click_menu,
        )
        self.bgcolor = ft.Colors.with_opacity(0.04, Colors.SYSTEM_BACKGROUND)

        notification_sender = NotificationSender()

        problems: list[str] = []

        if PLATFORM == 'Darwin':
            problems.append('Для MacOS в данный момент недоступен следующий функционал:\n - отслеживание активных окон\n - отслеживание времени бездействия')

        if USE_X11:
            try:
                subprocess.check_output(['xprintidle'], stderr=subprocess.DEVNULL)
            except Exception as e:
                problems.append('Для корректной работы трекера бездействия установите библиотеку xprintidle:\n- Debian: `apt install xprintidle`')

        if not IS_FFMPEG_INSTALLED:
            problems.append('Для работы звуковых уведомлений установите библиотеку ffmpeg:\n- Windows: `winget install ffmpeg`\n- Debian: `apt install ffmpeg`\n -Fedora: `dnf install ffmpeg`')

        if problems:
            self.actions = [
                ft.IconButton(
                    icon=Icons.ERROR,
                    tooltip='Проблемы',
                    on_click=lambda _: notification_sender.send_error(message='\n'.join([f'{index + 1}: {it}' for index, it in enumerate(problems)])),
                )
            ]

    async def _on_click_menu(self):
        await self.page.show_drawer()

