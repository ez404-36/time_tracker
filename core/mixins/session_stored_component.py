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

    def __str__(self) -> str:
        content = getattr(self, 'content', None)
        controls = getattr(self, 'controls', None)

        data: dict[str, str | None] = {
            'value': getattr(self, 'value', None),
            'visible': getattr(self, 'visible', None),
        }

        if content is not None:
            data['content'] = content
        if controls is not None and isinstance(controls, list):
            data['controls'] = ', '.join([control.__class__.__name__ for control in controls])

        return f'{self.get_stored_name()}({data})'