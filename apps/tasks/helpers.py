from peewee import JOIN
from flet import Page

from apps.tasks.models import Task
from core.flet_helpers import get_from_store


def refresh_tasks_tab(
        page: Page,
        with_update_controls=True,
):
    """
    Производит выборку задач из БД и обновление компонентов на основе этих данных
    """

    from apps.tasks.controls.task_list_item import TaskListItem

    ChildrenTask = Task.alias()

    tasks_active_tab = get_from_store(page, 'TaskActiveTab')
    tasks_list_active_component = get_from_store(page, 'TaskListActive')
    tasks_list_done_component = get_from_store(page, 'TaskListDone')

    tasks = (
        Task.select()
        .where(Task.parent == None)
        .join(ChildrenTask, JOIN.LEFT_OUTER, on=(ChildrenTask.parent_id == Task.id))
        .order_by(Task.created_at.desc(), Task.is_done)
        .group_by(Task.id)
    )

    active_tasks_controls = []
    done_tasks_controls = []

    for task in tasks:
        controls_list = done_tasks_controls if task.is_done else active_tasks_controls
        controls_list.append(
            TaskListItem(instance=task)
        )

    if tasks_list_active_component:
        tasks_list_active_component.controls = active_tasks_controls
        if with_update_controls:
            tasks_list_active_component.update()

    if tasks_list_done_component:
        tasks_list_done_component.controls = done_tasks_controls
        if with_update_controls:
            tasks_list_done_component.update()

    if tasks_active_tab:
        if with_update_controls:
            tasks_active_tab.update()
        else:
            tasks_active_tab.label = tasks_active_tab.get_label()
