import flet as ft

from core.di import container
from core.store import SessionStore


class SessionStoredComponent(ft.Control):
    """
    Компонент, сохраняемый в хранилище текущей сессии
    """

    def build(self):
        super().build()
        store: SessionStore = container.session_store
        store.set(self.get_stored_name(), self)

    def get_stored_name(self) -> str:
        return self.__class__.__name__