import abc
from typing import TypedDict


class WindowData(TypedDict):
    executable_name: str
    window_title: str | None
    executable_path: str | None


class WindowControlAbstract(abc.ABC):
    @abc.abstractmethod
    def get_active_window(self) -> WindowData | None: ...

    @abc.abstractmethod
    def get_all_windows(self) -> list[WindowData]: ...

    @abc.abstractmethod
    def get_idle_seconds(self) -> int: ...
