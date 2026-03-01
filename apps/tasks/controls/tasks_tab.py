import flet as ft

from apps.tasks.controls.tasks_active_tab import TaskActiveTab
from apps.tasks.controls.tasks_list import TaskListActive, TaskListDone
from apps.tasks.controls.task_mutate_modal import TaskMutateModal


class TasksTabViewControl(ft.Container):
    parent: ft.Tab
    content: ft.Tabs

    def __init__(self, **kwargs):
        kwargs.setdefault('padding', 20)
        super().__init__(**kwargs)

        self._list_active = TaskListActive()
        self._list_done = TaskListDone()
        self._active_tab = TaskActiveTab()

    def build(self):
        tabs = ft.Tabs(
            selected_index=0,
            animation_duration=300,
            expand=True,
            length=2,
            content=ft.Column(
                controls=[
                    ft.TabBar(
                        tabs=[
                            self._active_tab,
                            ft.Tab(
                                label='Выполненные',
                            )
                        ]
                    ),
                    ft.TabBarView(
                        expand=True,
                        controls=[
                            ft.Column(
                                controls=[
                                    ft.TextButton(
                                        content='Добавить задачу',
                                        on_click=lambda e: self.page.show_dialog(TaskMutateModal())
                                    ),
                                    self._list_active,
                                ]
                            ),
                            self._list_done,
                        ]
                    )
                ]
            )
        )

        self.content = tabs
