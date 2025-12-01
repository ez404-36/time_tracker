from typing import Iterable, Self

import flet as ft

from controls.base_control import BaseControl
from helpers import ActivityTabHelpers, NewActivityModalHelpers, StateDBHelpers
from models import Action, Activity, ActivityActions, db
from state import NewActivityModalState, State


class BaseNewActivityModalControl(BaseControl):
    def __init__(self, state: State):
        super().__init__(state)
        self._state: NewActivityModalState = state['controls']['activity']['new_activity_modal']
        self._component: ft.Control | None = None


class NewActivityModalActionRowControl(BaseNewActivityModalControl):
    def init(self, default: str = None):
        selected_action_ids = NewActivityModalHelpers(self._state).get_selected_action_ids()
        actions_options = self._get_actions_options(selected_action_ids)

        def on_click_action_remove(e):
            self._state['actions_view'].controls.remove(self._component)
            self._state['add_action_row_button'].disabled = False

            self._global_state['page'].update(
                self._state['actions_view'],
                self._state['add_action_row_button'],
            )

        action_selector = ft.Dropdown(
            editable=False,
            options=actions_options,
            width=200,
            value=default,
            on_change=self._on_change_action_selector,
        )
        is_target_action_checkbox = ft.Checkbox(label='Полезное действие')
        other_action_delete_button = ft.IconButton(ft.Icons.REMOVE, on_click=on_click_action_remove)

        self._component = ft.Row(
            controls=[
                action_selector,
                is_target_action_checkbox,
                other_action_delete_button,
            ]
        )

        self._state['actions_view'].controls.append(self._component)
        self._state['actions_view'].update()

        return self

    def _on_change_action_selector(self, e):
        new_activity_title_input = self._state['activity_title_input']
        selected_action_ids = NewActivityModalHelpers(self._state).get_selected_action_ids()
        actions_options = self._get_actions_options(selected_action_ids)

        submit_button = self._state['submit_button']
        add_action_row_button = self._state['add_action_row_button']

        submit_button.disabled = not new_activity_title_input.value
        add_action_row_button.disabled = not actions_options

        self._global_state['page'].update(
            submit_button,
            add_action_row_button,
        )

    def _get_actions_options(self, exclude_ids: Iterable[int]) -> list[ft.DropdownOption]:
        return [
            ft.DropdownOption(
                key=it.id,
                content=ft.Text(
                    value=it.title
                ),
                text=it.title,
            )
            for it in self._global_state['db']['actions'].values()
            if it.id not in exclude_ids
        ]


class NewActivityModalControlNewActionView(BaseNewActivityModalControl):
    """
    Компонент создания нового действия в модалке добавления новой активности
    """

    def init(self) -> Self:
        self._state['new_action_view'] = ft.Row()

        self._init_new_action_input()
        self._init_new_action_button()

    def _init_new_action_input(self):
        self._state['new_action_input'] = ft.TextField(
            label='Новое действие',
            on_change=self._on_change_new_action_input,
        )

        self._state['new_action_view'].controls.append(self._state['new_action_input'])

    def _on_change_new_action_input(self, e):
        value = e.control.value.strip()

        all_action_titles = [
            action.title.lower()
            for action in self._global_state['db']['actions'].values()
        ]

        if value.lower() in all_action_titles:
            self._state['new_action_input'].error = 'Такое действие уже существует'
            self._state['new_action_input'].update()
        else:
            self._state['new_action_button'].disabled = False
            self._state['new_action_button'].update()

    def _init_new_action_button(self):
        self._state['new_action_button'] = ft.TextButton(
            'Добавить',
            disabled=True,
            on_click=self._on_click_add_new_action_button,
        )
        self._state['new_action_view'].controls.append(self._state['new_action_button'])

    def _on_click_add_new_action_button(self, e):
        value = self._state['new_action_input'].value.strip()
        created_action = Action.create(title=value)
        StateDBHelpers(self._global_state).refresh_actions()

        self._state['new_action_input'].value = ''
        self._state['new_action_button'].disabled = True
        self._state['add_action_row_button'].disabled = not set(self._global_state['db']['actions'].keys()) - {created_action.id}

        NewActivityModalActionRowControl(self._global_state).init(str(created_action.id))

        self._global_state['page'].update(
            self._state['new_action_input'],
            self._state['new_action_button'],
            self._state['add_action_row_button'],
        )


class NewActivityModalControlActionsView(BaseNewActivityModalControl):
    """
    Компонент действий в модалке создания активности
    """

    def __init__(self, state: State):
        super().__init__(state)
        self._new_action_view: NewActivityModalControlNewActionView | None = None

    @property
    def component(self) -> ft.Column:
        return self._state['actions_view']

    def init(self):
        self._state['actions_view'] = ft.Column()
        self._init_add_action_row_button()
        self._new_action_view = NewActivityModalControlNewActionView(self._global_state).init()

    def _init_add_action_row_button(self):
        actions_keys = self._global_state['db']['actions'].keys()

        self._state['add_action_row_button'] = ft.IconButton(
            ft.Icons.ADD,
            on_click=self._on_click_add_action_row_button,
            disabled=not actions_keys,
        )

    def _on_click_add_action_row_button(self, e):
        NewActivityModalActionRowControl(self._global_state).init()


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

    def init(self):
        self._init_submit_button()
        self._init_activity_title_input()
        self._actions_view_control = NewActivityModalControlActionsView(self._global_state).init()

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

        selected_actions_data = NewActivityModalHelpers(self._state).get_selected_action_ids_with_target_checkbox()

        main_activity_action, _ = Action.get_or_create(title=activity_title)

        new_activity = Activity.create(
            title=activity_title,
        )
        StateDBHelpers(self._global_state).refresh_activities()

        ActivityActions.create(
            activity=new_activity,
            action=main_activity_action,
            is_useful=True,
            is_target=True,
        )

        for action_data in selected_actions_data:
            ActivityActions.create(
                activity=new_activity,
                action_id=action_data[0],
                is_target=False,
                is_useful=action_data[1],
            )

        self._state['activity_title_input'].value = ''
        self._state['actions_view'].controls = []
        self._state['actions_view'].update()

        activity_selector = self._global_state['controls']['activity']['activity_tab']['activity_selector']

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
                        ft.Text('*Если действия нет в списке, добавь новое через форму ниже', size=12),
                        self._state['new_action_view'],
                        ft.Divider(),
                    ]
                )
            ),
            actions=[
                ft.TextButton('Отмена', on_click=lambda e: self._global_state['page'].close(self._state['modal'])),
                self._state['submit_button'],
            ],
        )
