import abc
from typing import TypedDict


class WindowData(TypedDict):
    app_name: str
    title: str


class WindowControlAbstract(abc.ABC):
    def get_active_window(self) -> WindowData | None: ...
    def get_all_windows(self) -> list[WindowData]: ...
    def get_idle_seconds(self) -> int: ...
