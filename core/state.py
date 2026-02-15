from typing import TypedDict, get_type_hints

import flet as ft

from apps.time_tracker.models import IdleSession, WindowSession
from apps.to_do.models import ToDo


class BaseTabState(TypedDict):
    db: dict
    controls: dict
    selected: dict


class ActivityTabSelectedState(TypedDict):
    window_session: WindowSession | None
    idle_session: IdleSession | None
    expanded_statistics: set[str]


class ActivityTabControlsState(TypedDict):
    # Таб "Активность"
    activity_tab: ft.Container | None
    # Блок "Статистика"
    statistics_view: ft.Column | None


class ActivityTabState(TypedDict):
    """Состояние таба Активности"""
    selected: ActivityTabSelectedState
    controls: ActivityTabControlsState


class ToDoTabControlsState(TypedDict):
    list_active: ft.Column | None
    list_done: ft.Column | None


class ToDoDBState(TypedDict):
    todos: dict[int, ToDo]


class TodoTabState(TypedDict):
    """Состояние таба ТУ-ДУ"""
    controls: ToDoTabControlsState
    db: ToDoDBState
    expanded: set[int]


class TabsState(TypedDict):
    activity: ActivityTabState
    todo: TodoTabState


class State(TypedDict):
    tabs: TabsState


def init_state(typed_dict_class) -> State:
    """Рекурсивно инициализирует TypedDict со всеми значениями None"""
    result = {}
    type_hints = get_type_hints(typed_dict_class)

    for key, type_hint in type_hints.items():
        # Проверяем, является ли тип TypedDict
        if hasattr(type_hint, '__annotations__'):
            # Рекурсивно инициализируем вложенный TypedDict
            result[key] = init_state(type_hint)
        elif type_hint == set[int] or type_hint == set[str]:
            result[key] = set()
        else:
            # Для обычных типов ставим None
            result[key] = None

    return State(**result)  # noqa
