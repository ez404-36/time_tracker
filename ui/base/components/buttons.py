import flet as ft

from ui.base.style.button import get_text_button_style
from ui.consts import Colors, Icons


class SaveButton(ft.TextButton):
    def build(self):
        self.content = 'Сохранить'
        self.icon = Icons.SAVE
        self.style = get_text_button_style(Colors.BLUE)


class CancelButton(ft.TextButton):
    def build(self):
        self.content = 'Отмена'
        self.icon = Icons.CANCEL
        self.style = get_text_button_style(Colors.RED)
