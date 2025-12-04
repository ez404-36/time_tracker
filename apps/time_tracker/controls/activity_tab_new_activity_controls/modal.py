import flet as ft

from apps.time_tracker.controls.activity_tab_new_activity_controls.base import BaseNewActivityModalControl
from apps.time_tracker.controls.activity_tab_new_activity_controls.new_action_row import \
    NewActivityModalActionRowControl
from apps.time_tracker.controls.activity_tab_new_activity_controls.new_actions_view import \
    NewActivityModalControlActionsView
from apps.time_tracker.helpers import ActivityTabHelpers, NewActivityModalHelpers, StateDBHelpers
from apps.time_tracker.models import Action, Activity
from core.models import db
from core.state import State


class NewActivityModalControl(BaseNewActivityModalControl):
    """
    Модалка добавления новой активности
    """

    def __init__(self, state: State):
        super().__init__(state)
        self._actions_view_control: NewActivityModalControlActionsView | None = None
        self._main_action_row_control: NewActivityModalActionRowControl | None = None

    @property
    def component(self) -> ft.AlertDialog:
        return self._state['modal']

    def build(self):
        self._init_submit_button()
        self._init_activity_title_input()
        self._actions_view_control = NewActivityModalControlActionsView(self._global_state).build()

        self._init_modal()

        return self

    def _init_submit_button(self):
        self._state['submit_button'] = ft.TextButton(
            "Сохранить",
            on_click=self._on_click_submit_button,
            disabled=True,
        )

    @db.atomic()
    def _on_click_submit_button(self, e):
        activity_title: str = self._state['activity_title_input'].value

        selected_actions_data = NewActivityModalHelpers(self._state).get_actions_with_useful_checkbox()

        new_activity = Activity.create(
            title=activity_title,
        )
        StateDBHelpers(self._global_state).refresh_activities()

        Action.create(
            activity=new_activity,
            title=activity_title,
            is_useful=True,
            is_target=True,
        )

        for action_data in selected_actions_data:
            Action.create(
                activity=new_activity,
                title=action_data[0],
                is_target=False,
                is_useful=action_data[1],
            )

        self._state['activity_title_input'].value = ''
        self._state['actions_view'].controls = []
        self._state['actions_view'].update()

        activity_selector = self._global_state['tabs']['activity']['controls']['view']['activity_selector']

        activity_selector.disabled = False
        activity_selector.tooltip = None
        activity_selector.label = 'Чем сегодня займемся?'
        ActivityTabHelpers(self._global_state).refresh_activity_selector_options()

        self._global_state['page'].close(self._state['modal'])

    def _init_activity_title_input(self):
        self._state['activity_title_input'] = ft.TextField(
            label='Чем планируешь заняться?',
            hint_text='Например, работа',
            on_change=self._on_change_activity_title_input,
        )

    def _on_change_activity_title_input(self, e):
        submit_button = self._state['submit_button']

        submit_button.disabled = not e.control.value
        submit_button.update()

    def _init_modal(self):
        self._state['modal'] = ft.AlertDialog(
            modal=True,
            adaptive=True,
            title=ft.Text("Добавить новую активность"),
            content=ft.Container(
                width=500,
                height=500,
                padding=10,
                content=ft.Column(
                    controls=[
                        self._state['activity_title_input'],
                        ft.Divider(),
                        ft.Row(
                            controls=[
                                ft.Text(
                                    'Укажи все действия, \nкоторыми ещё можешь заниматься \nв момент этой активности.',
                                    size=14,
                                ),
                                self._state['add_action_row_button'],
                            ]
                        ),
                        self._state['actions_view'],
                        ft.Divider(),
                    ]
                )
            ),
            actions=[
                ft.TextButton('Отмена', on_click=lambda e: self._global_state['page'].close(self._state['modal'])),
                self._state['submit_button'],
            ],
        )
