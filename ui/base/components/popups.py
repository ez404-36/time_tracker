import abc

import flet as ft

from ui.consts import Colors, Icons, FontSize


class BasePopup(ft.AlertDialog, metaclass=abc.ABCMeta):
    def __init__(self, message: str, actions: list[ft.Control] = None, **kwargs):
        super().__init__(**kwargs)
        self._msg: str = message
        self._actions: list[ft.Control] | None = actions

    def build(self):
        self.title = ft.Row(
            controls=[
                self._get_icon(),
                ft.Text(value=self._msg)
            ]
        )
        self.actions = self._actions

    @abc.abstractmethod
    def _get_icon(self) -> ft.Icon: ...


class ErrorPopup(BasePopup):
    def _get_icon(self) -> ft.Icon:
        return ft.Icon(icon=Icons.ERROR, color=Colors.RED_LIGHT, size=FontSize.H1)


class InfoPopup(BasePopup):
    def _get_icon(self) -> ft.Icon:
        return ft.Icon(icon=Icons.INFO, color=Colors.BLUE_LIGHT, size=FontSize.H1)
