from typing import Optional

import flet as ft

from apps.time_tracker.controls.mutate_modal.new_action_row import \
    NewActivityModalActionRowControl
from apps.time_tracker.helpers import ActivityTabHelpers, TimeTrackDBHelpers
from apps.time_tracker.models import Action, Activity
from core.models import db
from core.state import ActivityTabState


class MutateActivityModalControl(ft.AlertDialog):
    """
    Модалка добавления/редактирования активности
    """

    def __init__(self, state: ActivityTabState, instance: Optional[Activity] = None, **kwargs):
        kwargs.setdefault('modal', True)
        kwargs.setdefault('adaptive', True)
        if instance:
            title = 'Редактировать активность'
        else:
            title = 'Добавить новую активность'
        kwargs.setdefault('title', title)
        super().__init__(**kwargs)
        self._state = state
        self._instance = instance

        self._title_input: ft.TextField | None = None
        self._add_action_button: ft.IconButton | None = None
        self._actions_view_control: ft.Column | None = None
        self._main_action_row_control: NewActivityModalActionRowControl | None = None
        self._submit: ft.TextButton | None = None

    def build(self):
        self._init_submit_button()
        self._init_activity_title_input()
        self._init_add_action_button()
        self._init_actions_view()

        controls = self.get_controls()

        self.content = ft.Container(
            width=500,
            height=500,
            padding=10,
            content=ft.Column(
                controls=controls,
            ),
        )
        self.actions = [
            ft.TextButton('Отмена', on_click=lambda e: self.page.close(self)),
            self._submit,
        ]

    def _init_submit_button(self):
        self._submit = ft.TextButton(
            "Сохранить",
            on_click=self._on_click_submit_button,
            disabled=not self._instance,
        )

    def _init_actions_view(self):
        self._actions_view_control = ft.Column()

        if self._instance:
            for action in self._instance.actions:
                action_row = NewActivityModalActionRowControl(self._state, action)
                self._actions_view_control.controls.append(action_row)

    def _init_add_action_button(self):
        self._add_action_button = ft.IconButton(
            ft.Icons.ADD,
            on_click=self._on_click_add_action_row_button,
        )

    @db.atomic()
    def _on_click_submit_button(self, e):
        activity_title: str = self._title_input.value

        if not self._instance:
            selected_actions_data = [
                (it.controls[0].value, it.controls[1].value)
                for it in self._actions_view_control.controls
            ]

            activity = Activity.create(
                title=activity_title,
            )
            TimeTrackDBHelpers(self._state).refresh_activities()

            to_create_actions = []

            to_create_actions.append(
                Action(
                    activity=activity,
                    title=activity_title,
                    is_useful=True,
                    is_target=True,
                )
            )

            for action_data in selected_actions_data:
                to_create_actions.append(
                    Action(
                        activity=activity,
                        title=action_data[0],
                        is_target=False,
                        is_useful=action_data[1],
                    )
                )

            Action.bulk_create(to_create_actions)
        else:
            self._instance.title = activity_title
            self._instance.save(only=['title'])
            TimeTrackDBHelpers(self._state).refresh_activities()

            to_delete = set([it.id for it in self._instance.actions])
            to_create = []
            to_update = []

            for control in self._actions_view_control.controls:
                title, is_useful = control.controls[0].value, control.controls[1].value

                if action := control._instance:
                    to_delete.discard(action.id)
                    action.title = title
                    action.is_useful = is_useful
                    to_update.append(action)
                else:
                    to_create.append(
                        Action(
                            activity=self._instance,
                            title=title,
                            is_useful=is_useful,
                            is_target=False,
                        )
                    )

            Action.bulk_update(to_update, fields=['title', 'is_useful'])
            Action.bulk_create(to_create)
            Action.delete().where(Action.id.in_(to_delete)).execute()

        self._title_input.value = ''
        self._actions_view_control.controls = []
        self._actions_view_control.update()

        activity_selector = self._state['controls']['view']['activity_selector']

        activity_selector.disabled = False
        activity_selector.tooltip = None
        activity_selector.label = 'Чем сегодня займемся?'
        ActivityTabHelpers(self._state).refresh_activity_selector_options()

        self.page.close(self)

    def _on_click_add_action_row_button(self, e):
        new_action_row = NewActivityModalActionRowControl(self._state)
        self._actions_view_control.controls.append(new_action_row)

    def _init_activity_title_input(self):
        self._title_input = ft.TextField(
            label='Чем планируешь заняться?',
            hint_text='Например, работа',
            on_change=self._on_change_activity_title_input,
            value=self._instance.title if self._instance else None,
        )

    def _on_change_activity_title_input(self, e):
        submit_button = self._submit

        submit_button.disabled = not e.control.value
        submit_button.update()

    def get_controls(self) -> list[ft.Control]:
        return [
            self._title_input,
            ft.Divider(),
            ft.Row(
                controls=[
                    ft.Text(
                        'Укажи все действия, \nкоторыми ещё можешь заниматься \nв момент этой активности.',
                        size=14,
                    ),
                    self._add_action_button,
                ]
            ),
            self._actions_view_control,
            ft.Divider(),
        ]
