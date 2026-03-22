from typing import Any

import flet as ft


class SessionStore:
    """
    Хранилище текущей сессии
    """

    def __init__(self, page: ft.Page):
        self._store = page.session.store

    def __repr__(self) -> str:
        return f'SessionStore({self._store.get_keys()})'

    def set(self, key: str, value: Any) -> None:
        self._store.set(key, value)

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


class PersistentStore:
    """
    Постоянное хранилище
    """

    def __init__(self, page: ft.Page):
        self._store = page.shared_preferences

    async def set(self, key: str, value: Any) -> None:
        await self._store.set(key, value)

    async def get(self, key: str) -> Any:
        return await self._store.get(key)

    async def contains(self, key: str) -> bool:
        return await self._store.contains(key)

    async def remove(self, key: str) -> None:
        await self._store.remove(key)

    async def get_or_create(self, key: str, default_value: Any) -> Any:
        if not await self.contains(key):
            await self.set(key, default_value)

        return await self.get(key)

    async def clear(self):
        await self._store.clear()
