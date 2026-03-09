from typing import Any

import flet as ft

def add_to_store(page: ft.Page, key: str, value: Any) -> None:
    page.session.store.set(key, value)

def get_from_store(page: ft.Page, key: str) -> Any | None:
    return page.session.store.get(key)

def get_or_create_from_store(page: ft.Page, key: str, default_value: Any) -> Any:
    if not is_in_store(page, key):
        add_to_store(page, key, default_value)

    return get_from_store(page, key)

def remove_from_store(page: ft.Page, key: str) -> None:
    if is_in_store(page, key):
        page.session.store.remove(key)

def is_in_store(page: ft.Page, key: str) -> bool:
    return page.session.store.contains_key(key)

