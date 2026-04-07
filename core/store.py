from typing import Any

import flet as ft

from core.system_events.event_bus import EventBus
from core.system_events.types import SystemEvent, SystemEventUpdateSessionStoreData


class SessionStore:
    """
    Хранилище текущей сессии
    """

    def __init__(self, page: ft.Page, event_bus: EventBus):
        self._store = page.session.store
        self._event_bus = event_bus

    def set(self, key: str, value: Any) -> None:
        self._store.set(key, value)
        self._event_bus.publish(
            SystemEvent(
                type='app.update_session_store',
                data=SystemEventUpdateSessionStoreData(
                    key=key,
                    value=value,
                )
            )
        )

    def get(self, key: str) -> Any:
        return self._store.get(key)

    def contains(self, key: str) -> bool:
        return self._store.contains_key(key)

    def remove(self, key: str) -> None:
        if self.contains(key):
            self._store.remove(key)

    def get_or_create(self, key: str, default_value: Any) -> Any:
        if not self.contains(key):
            self.set(key, default_value)

        return self.get(key)

    def clear(self):
        self._store.clear()
