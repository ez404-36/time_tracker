from peewee import JOIN

from apps.to_do.models import ToDo
from core.state import TodoTabState


def refresh_todo_list(
        state: TodoTabState,
        with_update_controls=True,
):
    """
    :return: список активных и список завершенных дел
    """
    from apps.to_do.controls.todo_list_item import ToDoListItem

    ChildrenToDo = ToDo.alias()

    todo_list_active = state['controls']['list_active']
    todo_list_done = state['controls']['list_done']

    todos = (
        ToDo.select()
        .where(ToDo.parent == None)
        .join(ChildrenToDo, JOIN.LEFT_OUTER, on=(ChildrenToDo.parent_id == ToDo.id))
        .order_by(ToDo.created_at.desc(), ToDo.is_done)
        .group_by(ToDo.id)
    )

    active_todo_controls = []
    done_todo_controls = []

    for todo in todos:
        controls = done_todo_controls if todo.is_done else active_todo_controls
        controls.append(
            ToDoListItem(instance=todo, state=state)
        )

    if todo_list_active:
        todo_list_active.controls = active_todo_controls
        if with_update_controls:
            todo_list_active.update()

    if todo_list_done:
        todo_list_done.controls = done_todo_controls
        if with_update_controls:
            todo_list_done.update()
