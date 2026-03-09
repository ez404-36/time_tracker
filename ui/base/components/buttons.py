import flet as ft

from ui.consts import Colors, Icons


class SaveButton(ft.TextButton):
    def build(self):
        self.content = 'Сохранить'
        self.icon = Icons.SAVE


class CancelButton(ft.TextButton):
    def build(self):
        self.content = 'Отмена'
        self.icon = Icons.CANCEL
        self.style = ft.ButtonStyle(
            color=Colors.RED,
        )
