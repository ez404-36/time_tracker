import datetime

import flet as ft

from apps.settings.controls.modal import SettingsModal
from apps.time_tracker.consts import EventType, EventInitiator
from apps.time_tracker.controls.view.activity_tab import ActivityTabViewControl
from apps.time_tracker.models import Event
from apps.to_do.controls.todo_tab import TodoTabViewControl
from core.models import db
from core.scripts import create_tables
from core.state import State, init_state
from core.tasks import check_tasks_deadline

state: State = init_state(State)


class DesktopApp:
    def __init__(self, page: ft.Page):
        self.page: ft.Page = page

        self._open_settings_btn: ft.IconButton | None = None
        self._is_settings_open = False

        self._settings_modal: SettingsModal | None = None
        self._activity_tab_control: ActivityTabViewControl | None = None
        self._todo_tab_control: TodoTabViewControl | None = None

    def init(self):
        """
        Инициализация десктопного приложения:
        * первичная отрисовка компонентов
        * определение обработчиков кнопок и селекторов
        """

        page = self.page

        page.adaptive = True
        page.title = 'Персональный менеджер'
        page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        page.vertical_alignment = ft.MainAxisAlignment.START

        page.on_close = self.on_close_page

        self._build_open_settings_btn()

        self._activity_tab_control = ActivityTabViewControl(state)
        self._todo_tab_control = TodoTabViewControl(state)
        self._settings_modal = SettingsModal(on_close=self._close_settings)

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
                                label='Трекер активности',
                                icon=ft.Icons.TIMER,
                            ),
                            ft.Tab(
                                label='Задачи',
                                icon=ft.Icons.CHECK,
                            ),
                        ]
                    ),
                    ft.TabBarView(
                        expand=True,
                        controls=[
                            self._activity_tab_control,
                            self._todo_tab_control,
                        ]
                    ),
                ]
            ),
        )

        page.appbar = ft.AppBar(
            leading=None,
            title=ft.Text("Персональный менеджер"),
            actions=[
                self._open_settings_btn,
            ],
            bgcolor=ft.Colors.with_opacity(0.04, ft.CupertinoColors.SYSTEM_BACKGROUND),
        )


        page.add(tabs)

        page.run_task(check_tasks_deadline, page=page)

    def _close_settings(self):
        if self._is_settings_open:
            self.toggle_show_settings(False)
            self._is_settings_open = False

    def _build_open_settings_btn(self):
        self._open_settings_btn = ft.IconButton(
            icon=ft.Icons.SETTINGS_OUTLINED,
            tooltip='Настройки',
            on_click=self._on_click_open_settings,
        )

    def _on_click_open_settings(self, e):
        self._is_settings_open = not self._is_settings_open
        self.toggle_show_settings(self._is_settings_open)

    def toggle_show_settings(self, show: bool):
        if show:
            self.page.show_dialog(self._settings_modal)
        else:
            self.page.pop_dialog()

    def on_close_page(self):
        Event.create(type=EventType.CLOSE_APP, initiator=EventInitiator.USER)

        selected_sessions = state['tabs']['activity']['selected']

        now = datetime.datetime.now(datetime.UTC)

        if window_session := selected_sessions['window_session']:
            window_session.stop(now)

        if idle_session := selected_sessions['idle_session']:
            idle_session.stop(now)

        return True


async def main(page: ft.Page):
    create_tables(db)
    Event.create(type=EventType.OPEN_APP, initiator=EventInitiator.USER)
    app = DesktopApp(page)
    app.init()


ft.run(main=main, view=ft.AppView.FLET_APP)
