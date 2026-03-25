import flet as ft

from core.di import container
from core.settings import SNACKBAR_DURATION_SECONDS


def show_snackbar(
        message: str,
        duration: int = SNACKBAR_DURATION_SECONDS,
):
    page = container.page
    page.show_dialog(
        ft.SnackBar(
            content=message,
            duration=ft.Duration(seconds=duration)
        )
    )
