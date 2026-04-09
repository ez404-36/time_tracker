import datetime

import flet as ft

from apps.app_settings.controls.settings_view import SettingsView
from apps.app_settings.models import AppSettings
from apps.tasks.controls.tasks_tab.main_container import TasksTabViewControl
from apps.tasks.helpers import refresh_tasks_tab
from apps.time_tracker.controls.view.index import ActivityTabViewControl
from apps.time_tracker.models import IdleSession
from apps.time_tracker.models import WindowSession
from core.di import container
from core.store import SessionStore
from core.system_events.event_bus import EventBus
from core.system_events.types import SystemEvent, SystemEventTimestampData
from core.tasks import check_tasks_deadline
from manage import migrate
from ui.components.app_bar import AppBar
from ui.consts import Icons

ACTIVITY_TRACK_NAV_INDEX = 0
TASKS_NAV_INDEX = 1
APP_SETTINGS_INDEX = 2


class DesktopApp:
    def __init__(self, page: ft.Page):
        self.page: ft.Page = page
        self._store = container.session_store

        self._activity_tab_control: ActivityTabViewControl | None = None
        self._tasks_tab_control: TasksTabViewControl | None = None
        self._app_settings_control: SettingsView | None = None

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
        self._app_settings_control = SettingsView(
            visible=self._selected_nav_index == APP_SETTINGS_INDEX,
        )

        page.appbar = AppBar(title='Трекер активности')

        page.add(self._activity_tab_control)
        page.add(self._tasks_tab_control)
        page.add(self._app_settings_control)

        nav_bar = ft.NavigationDrawer(
            on_change=self._on_change_navigation_drawer,
            selected_index=self._selected_nav_index,
            controls=[
                ft.NavigationDrawerDestination(label='Трекер активности', icon=Icons.TIMER),
                ft.NavigationDrawerDestination(label='Задачи', icon=Icons.CHECK),
                ft.NavigationDrawerDestination(label='Настройки', icon=Icons.SETTINGS),
            ]
        )

        page.drawer = nav_bar

        refresh_tasks_tab(with_update_controls=False)

        page.run_task(check_tasks_deadline)

    async def _on_change_navigation_drawer(self, e: ft.Event[ft.NavigationDrawer]):
        new_nav_index = int(e.data)

        if new_nav_index == self._selected_nav_index:
            return

        self._selected_nav_index = new_nav_index

        if self._selected_nav_index == ACTIVITY_TRACK_NAV_INDEX:
            to_show_view = self._activity_tab_control
            to_hide_views = [self._tasks_tab_control, self._app_settings_control]
            app_bar_title = 'Трекер активности'
        elif self._selected_nav_index == TASKS_NAV_INDEX:
            to_show_view = self._tasks_tab_control
            to_hide_views = [self._activity_tab_control, self._app_settings_control]
            app_bar_title = 'Задачи'
        else:
            to_show_view = self._app_settings_control
            to_hide_views = [self._activity_tab_control, self._tasks_tab_control]
            app_bar_title = 'Настройки'

        to_show_view.visible = True
        for to_hide_view in to_hide_views:
            to_hide_view.visible = False

        self.page.appbar.title = app_bar_title

        await self.page.close_drawer()

    def on_close_page(self):
        now = datetime.datetime.now(datetime.UTC)

        container.event_bus.publish(
            SystemEvent(
                type='app.close',
                data=SystemEventTimestampData(ts=now),
            )
        )

        window_session: WindowSession | None = self._store.get('window_session')
        if window_session:
            window_session.stop(now)

        idle_session: IdleSession | None = self._store.get('idle_session')
        if idle_session:
            idle_session.stop(now)

        return True


async def main(page: ft.Page):
    from apps.events.subscribers import EventsSubscriber
    from apps.time_tracker.services.main_tracker import MainTracker
    from apps.notifications.subscribers import AudioNotificationSubscriber, SnackbarSubscriber

    migrate(None)

    event_bus = EventBus()
    app_settings = AppSettings.get_solo()
    session_store = SessionStore(page, event_bus)

    container.page = page
    container.app_settings = app_settings
    container.event_bus = event_bus
    container.session_store = session_store
    container.main_tracker = MainTracker(event_bus, app_settings, session_store)

    EventsSubscriber()
    AudioNotificationSubscriber()
    SnackbarSubscriber()

    event_bus.publish(
        SystemEvent(
            type='app.open',
            data=SystemEventTimestampData(),
        )
    )

    app = DesktopApp(page)
    app.init()


ft.run(main=main, view=ft.AppView.FLET_APP)
