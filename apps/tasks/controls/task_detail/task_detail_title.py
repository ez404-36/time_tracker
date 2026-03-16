import flet as ft

from apps.tasks.models import Task
from ui.consts import FontSize, Colors


class TaskDetailTitle(ft.Row):
    def __init__(self, task: Task, **kwargs):
        super().__init__(**kwargs)
        self.task = task

    def build(self):
        font_size = FontSize.H5 if not self.task.parent_id else FontSize.REGULAR

        text = ft.Text(
            value=f'(#{self.task.id}) {self.task.title}',
            size=font_size,
        )

        controls = []

        if deadline_str := self.task.deadline_str:
            deadline = ft.Text(
                f'[{deadline_str}]',
                weight=ft.FontWeight.W_500,
                size=font_size
            )
            controls.append(deadline)

        is_any_children_expired = any([child.is_expired for child in self.task.children])
        if is_any_children_expired and not self.task.is_expired:
            controls.append(
                ft.Icon(
                    icon=ft.Icons.WARNING,
                    color=Colors.RED_LIGHT,
                    tooltip='Одна или несколько вложенных задач просрочены',
                ),
            )

        controls.append(text)

        self.controls = controls