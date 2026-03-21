import flet as ft

from ui.base.components.popups import ErrorPopup, InfoPopup


class NotificationSender:
    """
    Отправляет текстовые уведомления пользователю
    """

    def __init__(self, page: ft.Page):
        self._page = page

    def send_error(self, message: str, actions: list[ft.Control] | None = None, **kwargs):
        popup = ErrorPopup(message=message, actions=actions, **kwargs)
        self._page.show_dialog(popup)

    def send_info(self, message: str, actions: list[ft.Control] | None = None, **kwargs):
        popup = InfoPopup(message=message, actions=actions, **kwargs)
        self._page.show_dialog(popup)
