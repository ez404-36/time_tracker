import flet as ft

from ui.consts import Colors


class BorderedContainer(ft.Container):
    def __init__(self, **kwargs):
        kwargs.update(
            border=ft.Border.all(1, Colors.GREY),
            border_radius=10,
        )
        super().__init__(**kwargs)
