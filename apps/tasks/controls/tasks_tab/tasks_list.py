import flet as ft

from ui.base.components.stored_component import StoredComponent


class TaskListBase(ft.Column):
    def __init__(self, **kwargs):
        kwargs.update(dict(
            height=300,
            scroll=ft.ScrollMode.ADAPTIVE,
            spacing=10,
        ))
        super().__init__(**kwargs)


class TaskListActive(TaskListBase, StoredComponent): ...
class TaskListDone(TaskListBase, StoredComponent): ...