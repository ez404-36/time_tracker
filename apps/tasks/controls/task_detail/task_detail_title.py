import flet as ft

from apps.tasks.models import Task
from ui.base.components.text import TextComponent
from ui.consts import FontSize, Colors, Icons, FontWeight


class TaskDetailTitle(ft.Row):
    def __init__(self, task: Task, **kwargs):
        super().__init__(**kwargs)
        self.task = task

    def build(self):
        font_size = FontSize.H5 if not self.task.parent_id else FontSize.REGULAR

        text = TextComponent(
            value=str(self.task),
            size=font_size,
        )

        controls = []

        if deadline_str := self.task.deadline_str:
            deadline = TextComponent(
                value=f'[{deadline_str}]',
                weight=FontWeight.W_500,
                size=font_size
            )
            controls.append(deadline)

        is_any_children_expired = any([child.is_expired for child in self.task.children])
        if is_any_children_expired and not self.task.is_expired:
            controls.append(
                ft.Icon(
                    icon=Icons.WARNING,
                    color=Colors.RED_LIGHT,
                    tooltip='Одна или несколько вложенных задач просрочены',
                ),
            )

        controls.append(text)

        self.controls = controls
