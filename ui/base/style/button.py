import flet as ft

from ui.consts import FontSize


def get_text_button_style(color: ft.Colors) -> ft.ButtonStyle:
    return ft.ButtonStyle(
        side=ft.BorderSide(
            color=color,
        ),
        text_style=ft.TextStyle(
            size=FontSize.H5,
        ),
        icon_size=FontSize.H3,
    )
