import flet as ft


class ListView(ft.ListView):
    def __init__(self, **kwargs):
        kwargs.setdefault('spacing', 10)
        kwargs.setdefault('expand', True)

        super().__init__(**kwargs)