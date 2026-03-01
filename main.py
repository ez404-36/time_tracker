import datetime

import flet as ft

from apps.time_tracker.consts import EventType, EventInitiator
from apps.time_tracker.controls.view.activity_tab import ActivityTabViewControl
from apps.time_tracker.models import Event
from apps.tasks.controls.tasks_tab import TasksTabViewControl
from apps.tasks.helpers import refresh_tasks_tab
from apps.time_tracker.models import IdleSession
from apps.time_tracker.models import WindowSession
from core.flet_helpers import get_from_store
from core.models import db
from core.scripts import create_tables
from core.tasks import check_tasks_deadline
from ui.components.app_bar import AppBar
from ui.consts import Icons

ACTIVITY_TRACK_NAV_INDEX = 0
TASKS_NAV_INDEX = 1


class DesktopApp:
    def __init__(self, page: ft.Page):
        self.page: ft.Page = page

        self._activity_tab_control: ActivityTabViewControl | None = None
        self._tasks_tab_control: TasksTabViewControl | None = None

        self._selected_nav_index: int = ACTIVITY_TRACK_NAV_INDEX

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

        self._activity_tab_control = ActivityTabViewControl(
            visible=self._selected_nav_index == ACTIVITY_TRACK_NAV_INDEX,
        )
        self._tasks_tab_control = TasksTabViewControl(
            visible=self._selected_nav_index == TASKS_NAV_INDEX,
        )

        page.appbar = AppBar(title='Трекер активности')

        page.add(self._activity_tab_control)
        page.add(self._tasks_tab_control)

        nav_bar = ft.NavigationDrawer(
            on_change=self._on_change_navigation_drawer,
            selected_index=self._selected_nav_index,
            controls=[
                ft.NavigationDrawerDestination(label='Трекер активности', icon=Icons.TIMER),
                ft.NavigationDrawerDestination(label='Задачи', icon=Icons.CHECK),
            ]
        )

        page.drawer = nav_bar

        refresh_tasks_tab(self.page, with_update_controls=False)

        page.run_task(check_tasks_deadline, page=page)

    async def _on_change_navigation_drawer(self, e: ft.Event[ft.NavigationDrawer]):
        new_nav_index = int(e.data)

        if new_nav_index == self._selected_nav_index:
            return

        self._selected_nav_index = new_nav_index

        if self._selected_nav_index == ACTIVITY_TRACK_NAV_INDEX:
            to_show_view = self._activity_tab_control
            to_hide_view = self._tasks_tab_control
            app_bar_title = 'Трекер активности'
        else:
            to_show_view = self._tasks_tab_control
            to_hide_view = self._activity_tab_control
            app_bar_title = 'Задачи'

        to_show_view.visible = True
        to_hide_view.visible = False

        self.page.appbar.title = app_bar_title

        await self.page.close_drawer()

    def on_close_page(self):
        Event.create(type=EventType.CLOSE_APP, initiator=EventInitiator.USER)

        now = datetime.datetime.now(datetime.UTC)

        window_session: WindowSession | None = get_from_store(self.page, 'window_session')
        if window_session:
            window_session.stop(now)

        idle_session: IdleSession | None = get_from_store(self.page, 'idle_session')
        if idle_session:
            idle_session.stop(now)

        return True


async def main(page: ft.Page):
    create_tables(db)
    Event.create(type=EventType.OPEN_APP, initiator=EventInitiator.USER)
    app = DesktopApp(page)
    app.init()


ft.run(main=main, view=ft.AppView.FLET_APP)
