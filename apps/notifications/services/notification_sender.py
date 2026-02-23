import flet as ft

from ui.popup.error import ErrorPopup


class NotificationSender:
    """
    Отправляет текстовые уведомления пользователю
    """

    def __init__(self, page: ft.Page):
        self._page = page

    def send(self, message: str):
        popup = ErrorPopup(message=message)
        self._page.show_dialog(popup)
