import flet as ft

from ui.consts import Colors


class ErrorPopup(ft.AlertDialog):
    def __init__(self, message: str, **kwargs):
        super().__init__(**kwargs)
        self._msg = message

    def build(self):
        self.title = ft.Row(
            controls=[
                ft.Icon(ft.Icons.ERROR, color=Colors.RED, size=48),
                ft.Text(self._msg)
            ]
        )