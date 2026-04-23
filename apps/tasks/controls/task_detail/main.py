import flet as ft

from apps.tasks.controls.task_detail.task_detail_title import TaskDetailTitle
from apps.tasks.controls.task_mutate.modal import TaskMutateModal
from apps.tasks.helpers import refresh_tasks_tab
from apps.tasks.models import Task
from core.database import db
from core.di import container
from core.system_events.types import SystemEvent, SystemEventTaskAction
from ui.base.components.text import TextComponent
from ui.consts import Colors, FontSize, Icons


class TaskListItem(ft.ExpansionTile):
    """
    Отображение одной задачи
    """

    def __init__(self, instance: Task, **kwargs):
        kwargs['title'] = None
        kwargs['dense'] = True
        kwargs['affinity'] = ft.TileAffinity.TRAILING

        super().__init__(**kwargs)
        self._instance = instance

        self._event_bus = container.event_bus

    def build(self):
        is_done = self._instance.is_done

        self.leading = ft.Checkbox(
            value=is_done,
            fill_color=Colors.GREY if is_done else None,
            on_change=self._on_change_checkbox,
        )

        self.bgcolor = Colors.RED_LIGHT if self._instance.is_expired else None
        self.collapsed_bgcolor = Colors.RED_LIGHT if self._instance.is_expired else None

        self.title = TaskDetailTitle(self._instance)

        self.subtitle = TextComponent(
            value=self._instance.description,
            size=FontSize.REGULAR if not self._instance.parent_id else FontSize.SMALL
        )

        self.trailing = ft.PopupMenuButton(
            icon=Icons.MORE_ACTIONS,
            items=self.get_popup_menu_items(),
        )

        children_tasks = self._instance.children

        self.controls = [
            self.__class__(instance=child, margin=ft.Margin(left=20))
            for child in children_tasks
        ]

    async def _on_change_checkbox(self, e):
        is_done = e.control.value
        self._instance.is_done = is_done

        with db.atomic():
            self._instance.save()
            if parent := self._instance.parent:
                has_opened_tasks = parent.children.where(Task.is_done != True).exists()
                if is_done and not has_opened_tasks:
                    parent.is_done = True
                    parent.save()
                elif not is_done and has_opened_tasks:
                    parent.is_done = False
                    parent.save()

        refresh_tasks_tab()

    async def _on_click_delete(self, e):
        instance_str = str(self._instance)

        children_ids = list(map(lambda it: it.id, self._instance.children.select(Task.id)))

        query = (
            Task
            .delete()
            .where(
                Task.id.in_(children_ids + [self._instance.id])
            )
        )
        query.execute()

        self._event_bus.publish(
            SystemEvent(
                type='tasks.delete',
                data=SystemEventTaskAction(
                    task=instance_str,
                )
            )
        )

        refresh_tasks_tab()

    def get_popup_menu_items(self) -> list[ft.PopupMenuItem]:
        edit_menu_item = ft.PopupMenuItem(
           icon=Icons.EDIT,
           content='Редактировать',
           on_click=lambda e: self.page.show_dialog(TaskMutateModal(instance=self._instance)),
        )

        add_children_menu_item = ft.PopupMenuItem(
            icon=Icons.ADD,
            content='Добавить вложенную задачу',
            on_click=lambda e: self.page.show_dialog(TaskMutateModal(parent_instance=self._instance)),
        )

        delete_menu_item = ft.PopupMenuItem(
            icon=Icons.DELETE,
            content='Удалить',
            on_click=self._on_click_delete,
        )

        items = [edit_menu_item]

        if not self._instance.parent_id:
            items.append(add_children_menu_item)

        items.append(delete_menu_item)

        return items

