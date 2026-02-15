import flet as ft

from core.settings import app_settings


class NotificationSender:
    """
    Отправляет уведомления пользователю.
    Текстовые и голосовые
    """

    def __init__(self, page: ft.Page, msg: str):
        self._page = page
        self._app_settings = app_settings
        self._msg = msg

    def show_snackbar(self):
        popup = ft.SnackBar(
            content=ft.Text(self._msg),
            open=True,
            show_close_icon=True,
        )
        self._page.snack_bar = popup

    def play_sound(self):
        pass
