import flet as ft

from core.flet_helpers import add_to_store


class StoredComponent(ft.Control):
    """
    Компонент, сохраняемый в хранилище текущей сессии
    """

    def build(self):
        super().build()
        add_to_store(self.page, self.get_stored_name(), self)

    def get_stored_name(self) -> str:
        return self.__class__.__name__