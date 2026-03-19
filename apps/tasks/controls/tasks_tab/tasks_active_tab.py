import flet as ft

from core.di import container
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
        store = container.store
        if active_tasks_list_component := store.get('TaskListActive'):
            active_tasks_len = len(active_tasks_list_component.controls)
        else:
            active_tasks_len = 0
        return f'Активные ({active_tasks_len})'