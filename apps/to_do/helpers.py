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
    from apps.to_do.controls.todo_row import ToDoTabToDoViewControl

    ChildrenToDo = ToDo.alias()

    todos = (
        ToDo.select()
        .where(ToDo.parent == None)
        .join(ChildrenToDo, JOIN.LEFT_OUTER, on=(ChildrenToDo.parent_id == ToDo.id))
        .order_by(ToDo.created_at.desc(), ToDo.is_done)
        .group_by(ToDo.id)
    )

    todo_list_active = state['controls']['list_active']
    todo_list_done = state['controls']['list_done']

    active_todo_controls = []
    done_todo_controls = []

    for todo in todos:
        controls = done_todo_controls if todo.is_done else active_todo_controls
        controls.append(
            ToDoTabToDoViewControl(instance=todo, state=state)
        )

    todo_list_active.controls = active_todo_controls
    todo_list_done.controls = done_todo_controls

    if with_update_controls:
        todo_list_active.update()
        todo_list_done.update()
