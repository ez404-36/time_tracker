import datetime

import flet as ft
from flet.core.types import AppView

from apps.settings.controls.modal import SettingsModal
from apps.settings.models import AppSettings
from apps.time_tracker.consts import EventType, EventInitiator
from apps.time_tracker.controls.view.activity_tab import ActivityTabViewControl
from apps.time_tracker.models import Event
from apps.to_do.controls.todo_tab import TodoTabViewControl
from core.models import db
from core.scripts import create_tables
from core.state import State, init_state

state: State = init_state(State)


class DesktopApp:
    def __init__(self, page: ft.Page):
        self.page: ft.Page = page

        self._open_settings_btn: ft.ElevatedButton | None = None
        self._is_settings_open = False
        self._app_settings: AppSettings | None = None

        self._settings_modal: SettingsModal | None = None
        self._activity_tab_control: ActivityTabViewControl | None = None
        self._todo_tab_control: TodoTabViewControl | None = None

    def init(self):
        """
        Инициализация десктопного приложения:
        * первичная отрисовка компонентов
        * определение обработчиков кнопок и селекторов
        """
        self._app_settings, _ = AppSettings.get_or_create()
        self._app_settings.detect_and_update_client_timezone()

        page = self.page

        page.title = 'Персональный менеджер'
        page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        page.vertical_alignment = ft.MainAxisAlignment.START

        page.on_disconnect = self.on_disconnect

        self._build_open_settings_btn()

        self._activity_tab_control = ActivityTabViewControl(state)
        self._todo_tab_control = TodoTabViewControl(state)
        self._settings_modal = SettingsModal(on_close=self._close_settings)

        tabs = ft.Tabs(
            selected_index=0,
            animation_duration=300,
            expand=1,
            tabs=[
                ft.Tab(
                    text='Трекер активности',
                    icon=ft.Icons.TIMER,
                    content=self._activity_tab_control,
                ),
                ft.Tab(
                    text='TODO',
                    content=self._todo_tab_control,
                )
            ]
        )


        page.add(self._open_settings_btn)
        page.add(tabs)

    def _close_settings(self):
        if self._is_settings_open:
            self.toggle_show_settings(False)
            self._is_settings_open = False

    def _build_open_settings_btn(self):
        self._open_settings_btn = ft.ElevatedButton(
            'Открыть настройки',
            on_click=self._on_click_open_settings,
        )

    def _on_click_open_settings(self, e):
        self._is_settings_open = not self._is_settings_open
        self.toggle_show_settings(self._is_settings_open)

    def toggle_show_settings(self, show: bool):
        if show:
            self.page.open(self._settings_modal)
        else:
            self.page.close(self._settings_modal)

    async def on_disconnect(self, e: ft.ControlEvent):
        Event.create(type=EventType.CLOSE_APP, initiator=EventInitiator.USER)

        if e.name == 'disconnect':
            selected_sessions = state['tabs']['activity']['selected']

            now = datetime.datetime.now(datetime.UTC)

            if window_session := selected_sessions['window_session']:
                window_session.stop(now)

            if idle_session := selected_sessions['idle_session']:
                idle_session.stop(now)

        return True


def main(page: ft.Page):
    app = DesktopApp(page)
    app.init()


if __name__ == "__main__":
    create_tables(db)
    Event.create(type=EventType.OPEN_APP, initiator=EventInitiator.USER)
    ft.app(target=main, view=AppView.FLET_APP)

