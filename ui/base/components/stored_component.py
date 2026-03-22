import flet as ft

from core.di import container
from core.store import Store


class StoredComponent(ft.Control):
    """
    Компонент, сохраняемый в хранилище текущей сессии
    """

    def build(self):
        super().build()
        store: Store = container.store
        store.set(self.get_stored_name(), self)

    def get_stored_name(self) -> str:
        return self.__class__.__name__