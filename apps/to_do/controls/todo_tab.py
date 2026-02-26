import flet as ft

from apps.to_do.controls.todo_mutate_modal import ToDoMutateModal
from apps.to_do.helpers import refresh_todo_list
from core.state import State, TodoTabState


class TodoTabViewControl(ft.Container):
    parent: ft.Tab
    content: ft.Tabs

    def __init__(self, state: State, **kwargs):
        kwargs.setdefault('padding', 20)
        super().__init__(**kwargs)
        self._state: TodoTabState = state['tabs']['todo']

        self._list_active: ft.Column | None = None
        self._list_done: ft.Column | None = None

    def build(self):
        self._list_active = ft.Column(
            height=300,
            scroll=ft.ScrollMode.ADAPTIVE,
            spacing=10,
        )
        self._list_done = ft.Column(
            height=300,
            scroll=ft.ScrollMode.ADAPTIVE,
            spacing=10,
        )

        self._state['controls']['list_active'] = self._list_active
        self._state['controls']['list_done'] = self._list_done

        refresh_todo_list(self._state, with_update_controls=False)

        tabs = ft.Tabs(
            selected_index=0,
            animation_duration=300,
            expand=True,
            length=2,
            content=ft.Column(
                controls=[
                    ft.TabBar(
                        tabs=[
                            ft.Tab(
                                label=f'Активные ({len(self._list_active.controls)})',
                            ),
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
                                        on_click=lambda e: self.page.show_dialog(ToDoMutateModal(self._state))
                                    ),
                                    self._list_active,
                                ]
                            ),
                            # self._list_active,
                            self._list_done,
                        ]
                    )
                ]
            )
        )

        # self.content = ft.Row(
        #     controls=[
        #         ft.Column(
        #             width=400,
        #             controls=[
        #                 ft.TextButton(
        #                     content='Добавить задачу',
        #                     on_click=lambda e: self.page.show_dialog(ToDoMutateModal(self._state))
        #                 ),
        #                 self._list_active,
        #             ]
        #         ),
        #         ft.VerticalDivider(),
        #         ft.Column(
        #             controls=[
        #                 ft.Text('Завершено', size=20, weight=ft.FontWeight.BOLD),
        #                 self._list_done,
        #             ]
        #         ),
        #     ]
        # )

        self.content = tabs
