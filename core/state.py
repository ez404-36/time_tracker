from typing import TypedDict, get_type_hints

import flet as ft

from apps.time_tracker.models import Activity, ActivityDayTrack
from apps.to_do.models import ToDo


class BaseTabState(TypedDict):
    db: dict
    controls: dict
    selected: dict


class ActivityTabDBState(TypedDict):
    activities: dict[int, Activity]


class ActivityTabSelectedState(TypedDict):
    activity: Activity | None   # выбранная активность
    day_track: ActivityDayTrack | None    # текущий объект отслеживания активности за день
    application_id: str | None


class ActivityTabActivityViewState(TypedDict):
    tab: ft.Container | None
    activity_actions_row: ft.Row | None
    activity_selector: ft.Dropdown | None
    new_activity_button: ft.ElevatedButton | None
    actions_view: ft.Column | None
    active_action_timer: ft.Text | None


class ActivityTabMutateActivityModalState(TypedDict):
    """Состояние модалки добавления/редактирования активности"""
    modal: ft.AlertDialog | None
    activity_title_input: ft.TextField | None
    submit_button: ft.TextButton | None


class ActivityTabControlsState(TypedDict):
    new_activity: ActivityTabMutateActivityModalState
    view: ActivityTabActivityViewState


class ActivityTabState(TypedDict):
    """Состояние таба Активности"""
    db: ActivityTabDBState
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
        elif type_hint == set[int]:
            result[key] = set()
        else:
            # Для обычных типов ставим None
            result[key] = None

    return State(**result)  # noqa
