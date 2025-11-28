from typing import TypedDict, get_type_hints

import flet as ft

from models import Action, Activity, ActivityTrack


class StateDB(TypedDict):
    actions: dict[int, Action]
    activities: dict[int, Activity]


class StateSelected(TypedDict):
    activity: Activity | None   # выбранная активность
    activity_track: ActivityTrack | None    # текущий объект отслеживания активности за день
    action: Action | None   # текущее активное действие


class NewActivityModalState(TypedDict):
    """Состояние модалки добавления новой активности"""
    modal: ft.AlertDialog | None
    activity_title_input: ft.TextField | None
    actions_view: ft.Column | None
    new_action_view: ft.Row | None
    add_action_row_button: ft.IconButton | None
    new_action_input: ft.TextField | None
    new_action_button: ft.TextButton | None
    submit_button: ft.TextButton | None


class ActivityTabActivityTrackState(TypedDict):
    """
    Состояние компонентов отслеживания активности
    """
    actions_view: ft.Column | None
    active_action_timer: ft.Text | None


class ActivityTabState(TypedDict):
    tab: ft.Column | None
    activity_actions_row: ft.Row | None
    activity_selector: ft.Dropdown | None
    # start_button: ft.IconButton | None
    # pause_button: ft.IconButton | None
    # stop_button: ft.IconButton | None
    new_activity_button: ft.ElevatedButton | None


class ActivityTabControlsState(TypedDict):
    """Состояние таба Активности"""
    activity_tab: ActivityTabState
    new_activity_modal: NewActivityModalState
    activity_track: ActivityTabActivityTrackState


class ToDoTabControlsState(TypedDict):
    """Состояние ТУ-ДУ таба"""
    todo_tab: ft.Column | None
    todo_view: ft.Column | None
    todo_input: ft.TextField | None
    todo_submit: ft.FloatingActionButton | None
    todo_list: ft.Column | None


class ControlsState(TypedDict):
    activity: ActivityTabControlsState
    todo: ToDoTabControlsState


class State(TypedDict):
    page: ft.Page | None
    selected: StateSelected  # выбранные значения в инпутах/селекторах
    controls: ControlsState  # flet компоненты
    db: StateDB    # данные из БД
    activity_track_actions_time: dict[str | int, int]


def init_state(typed_dict_class) -> State:
    """Рекурсивно инициализирует TypedDict со всеми значениями None"""
    result = {}
    type_hints = get_type_hints(typed_dict_class)

    for key, type_hint in type_hints.items():
        # Проверяем, является ли тип TypedDict
        if hasattr(type_hint, '__annotations__'):
            # Рекурсивно инициализируем вложенный TypedDict
            result[key] = init_state(type_hint)
        else:
            # Для обычных типов ставим None
            result[key] = None

    return result
