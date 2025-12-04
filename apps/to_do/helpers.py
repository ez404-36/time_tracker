import flet as ft

from apps.to_do.models import ToDo
from core.state import TodoTabState


def refresh_todo_list(
        state: TodoTabState,
        todo_row_control: type[ft.Row],
        with_update_controls=True,
):
    """
    :return: список активных и список завершенных дел
    """

    todos = ToDo.select().order_by(ToDo.created_at.desc(), ToDo.is_done)

    todo_list_active = state['controls']['list_active']
    todo_list_done = state['controls']['list_done']

    active_todo_controls = []
    done_todo_controls = []

    for todo in todos:
        controls = done_todo_controls if todo.is_done else active_todo_controls
        controls.append(
            todo_row_control(instance=todo, state=state)
        )

    todo_list_active.controls = active_todo_controls
    todo_list_done.controls = done_todo_controls

    if with_update_controls:
        todo_list_active.update()
        todo_list_done.update()
