import flet as ft


class NotificationSender:
    """
    Отправляет текстовые уведомления пользователю
    """

    def __init__(self, page: ft.Page, msg: str):
        self._page = page
        self._msg = msg

    def send(self):
        popup = ft.AlertDialog(
            title=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.ERROR, color=ft.Colors.RED_300, size=48),
                    ft.Text(self._msg)
                ]
            ),
        )
        self._page.open(popup)
