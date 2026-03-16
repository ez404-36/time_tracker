import flet as ft

from core.flet_helpers import get_from_store
from ui.base.components.stored_component import StoredComponent


class TaskActiveTab(ft.Tab, StoredComponent):
    """
    Компонент таба "Активные задачи"
    """

    def build(self):
        self.label = self.get_label()
        super().build()

    def update(self):
        self.label = self.get_label()
        super().update()

    def get_label(self) -> str:
        if active_tasks_list_component := get_from_store(self.page, 'TaskListActive'):
            active_tasks_len = len(active_tasks_list_component.controls)
        else:
            active_tasks_len = 0
        return f'Активные ({active_tasks_len})'