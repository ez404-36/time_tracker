import asyncio
import datetime

import flet as ft

from apps.app_settings.models import AppSettings
from apps.time_tracker.controls.statistics.index import ActivityStatisticsView
from apps.time_tracker.controls.view.opened_windows import OpenedWindowsComponent
from core.di import container
from ui.components.timer import TimerComponent
from apps.time_tracker.models import IdleSession, WindowSession
from apps.time_tracker.services.activity_tracker import ActivityTracker
from apps.time_tracker.services.window_control.abstract import WindowData
from apps.time_tracker.utils import get_app_name_and_transform_window_title
from ui.base.components.stored_component import StoredComponent
from ui.consts import Colors, Icons


class ActivityTabViewControl(ft.Container, StoredComponent):
    """Таб активности"""

    parent: ft.Tab
    content: ft.Row

    def __init__(self, **kwargs):
        kwargs.setdefault('padding', 20)
        super().__init__(**kwargs)
        self._store = container.store

        self._tracking_status: ft.Text | None = None
        self._start_button: ft.IconButton | None = None
        self._stop_button: ft.IconButton | None = None

        self.window_session_ctrl: ft.Column | None = None
        self.idle_session_ctrl: ft.Column | None = None
        self._statistics_view: ActivityStatisticsView | None = None
        self.opened_windows_component: OpenedWindowsComponent | None = None

        self._window_session: WindowSession | None = None
        self._idle_session: IdleSession | None = None
        self._autorefresh_statistics_task: asyncio.Task | None = None
        self._current_window_data: WindowData | None = None  # данные текущего окна, полученные из трекера

        self._app_settings = AppSettings.get_solo()
        self.tracker: ActivityTracker | None = None

    @property
    def is_activity_tracker_enabled(self) -> bool:
        return self._store.get_or_create('is_activity_tracker_enabled', False)

    def build(self):
        self.tracker = ActivityTracker()
        self._store.add('activity_tracker', self.tracker)

        self.opened_windows_component = OpenedWindowsComponent()

        self.rebuild_tracking_status_text()
        self._start_button = ft.IconButton(
            icon=ft.Icon(
                icon=Icons.START,
                color=Colors.GREEN_LIGHT,
            ),
            on_click=self._on_click_start,
            tooltip='Включить'
        )
        self._stop_button = ft.IconButton(
            icon=ft.Icon(
                icon=Icons.STOP,
                color=Colors.RED_LIGHT,
            ),
            visible=False,
            on_click=self._on_click_stop,
            tooltip='Выключить',
        )

        self.window_session_ctrl = ft.Column(visible=False)
        self.idle_session_ctrl = ft.Column(visible=False)

        time_tracking_column = ft.Column(
            width=600,
            controls=[
                ft.Row([
                    self._start_button,
                    self._stop_button,
                    self._tracking_status,
                ]),
                self.window_session_ctrl,
                self.idle_session_ctrl,
                ft.Divider(),
                self.opened_windows_component,
            ]
        )

        self._statistics_view = ActivityStatisticsView()

        self.content = ft.Row(
            vertical_alignment=ft.CrossAxisAlignment.START,
            controls=[
                time_tracking_column,
                ft.VerticalDivider(),
                self._statistics_view,
            ]
        )
        super().build()

    def rebuild_tracking_status_text(self):
        title = self.get_status_title()
        if not self._tracking_status:
            self._tracking_status = ft.Text(
                value=title,
                size=16,
            )
        else:
            self._tracking_status.value = title

    def get_status_title(self):
        if self.is_activity_tracker_enabled:
            return 'Отслеживание активности...'
        else:
            return 'Отслеживание активности выключено'

    async def _on_click_start(self, e):
        self._store.add('is_activity_tracker_enabled', True)

        if self.opened_windows_component.is_active_windows_showed:
            if self._current_window_data:
                self.switch_window_session(self._current_window_data, datetime.datetime.now(datetime.UTC))
        else:
            await self.tracker.start()

        await self._toggle_affected_on_start_stop()

    async def _on_click_stop(self, e):
        if self.opened_windows_component.is_active_windows_showed:
            await self.stop_tracking(datetime.datetime.now(datetime.UTC))
        else:
            await self.tracker.stop()

    async def _toggle_affected_on_start_stop(self):
        is_start = self.is_activity_tracker_enabled

        self._start_button.visible = not is_start
        self._stop_button.visible = is_start
        self.rebuild_tracking_status_text()
        self.window_session_ctrl.visible = is_start
        self.idle_session_ctrl.visible = is_start

        if is_start:
            self._statistics_view.toggle_show_statistics(force_show=True)
            self._autorefresh_statistics_task = asyncio.create_task(self._run_auto_refresh_statistics())
        else:
            if self._autorefresh_statistics_task:
                await self._autorefresh_statistics_task

        self.update()

    # TODO: большая нагрузка при рефреше статистики: каждую секунду перезапрос в БД и отрисовка.
    #  Пока некритично
    async def _run_auto_refresh_statistics(self):
        while self.is_activity_tracker_enabled:
            self._statistics_view.refresh_statistics()
            await asyncio.sleep(1)

    def create_idle_session(self, ts: datetime.datetime):
        if not self.is_activity_tracker_enabled:
            return

        self._idle_session = IdleSession.create(start_ts=ts)
        self._store.add('idle_session', self._idle_session)
        self._app_settings.play_idle_start_sound()

        idle_session_control = self.idle_session_ctrl
        idle_session_control.controls.clear()
        if self._idle_session:
            idle_session_control.controls.extend([
                TimerComponent(),
                ft.Text(
                    value='Бездействие',
                    color=Colors.RED_LIGHT,
                )
            ])
        idle_session_control.update()

    def switch_window_session(self, window: WindowData, ts: datetime.datetime):
        self._current_window_data = window
        if not self.is_activity_tracker_enabled:
            return

        _, title = get_app_name_and_transform_window_title(window['executable_name'], window['window_title'])

        if self._window_session:
            self._window_session.stop(ts)

        self._window_session = WindowSession.create(
            executable_name=window['executable_name'],
            executable_path=window['executable_path'],
            window_title=title,
            start_ts=ts,
        )

        self._store.add('window_session', self._window_session)

        window_session_control = self.window_session_ctrl

        window_session_control.controls.clear()

        app_title = self._window_session.app_name
        if self._window_session.window_title:
            app_title += f' ({self._window_session.window_title})'

        window_session_control.controls.extend([
            TimerComponent(),
            ft.Text(
                value=app_title,
            )
        ])
        window_session_control.update()

    def stop_idle_session(self, ts: datetime.datetime):
        if not self.is_activity_tracker_enabled:
            return

        if self._idle_session:
            self._idle_session.stop(ts)

        self._idle_session = None
        self._store.remove('idle_session')
        self.idle_session_ctrl.controls.clear()
        self.idle_session_ctrl.update()

    async def stop_tracking(self, ts: datetime.datetime):
        self.stop_window_session(ts)
        self.stop_idle_session(ts)
        self._store.add('is_activity_tracker_enabled', False)
        await self._toggle_affected_on_start_stop()

    def stop_window_session(self, ts: datetime.datetime):
        if not self.is_activity_tracker_enabled:
            return

        if self._window_session:
            self._window_session.stop(ts)

        self._window_session = None
        self._store.remove('window_session')
        self.window_session_ctrl.controls.clear()
        self.window_session_ctrl.update()
