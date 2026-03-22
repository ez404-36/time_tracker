from typing import Any

import flet as ft


class Store:
    def __init__(self, page: ft.Page):
        self._store = page.session.store

    def __repr__(self) -> str:
        return f'Store({self._store.get_keys()})'

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
