import asyncio
import datetime

import flet as ft

from apps.notifications.services.notification_sender import NotificationSender
from apps.time_tracker.controls.statistics.index import ActivityStatisticsView
from apps.time_tracker.controls.view.opened_windows import OpenedWindowsComponent
from apps.time_tracker.controls.view.total_time import TotalTimeComponent
from apps.time_tracker.models import WindowSession, IdleSession
from apps.time_tracker.services.activity_tracker import ActivityTracker
from apps.time_tracker.services.window_control.abstract import WindowData
from apps.time_tracker.utils import get_app_name_and_transform_window_title
from core.di import container
from ui.base.components.stored_component import StoredComponent
from ui.components.timer import TimerComponent
from ui.consts import Icons, Colors, FontSize


class TimeTrackingComponent(ft.Column, StoredComponent):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._store = container.store
        self._app_settings = container.app_settings

        self._tracking_status: ft.Text | None = None
        self._start_button: ft.IconButton | None = None
        self._stop_button: ft.IconButton | None = None

        self._total_time_component: TotalTimeComponent | None = None

        self._main_row: ft.Row | None = None

        self.window_session_ctrl: ft.Column | None = None
        self.idle_session_ctrl: ft.Column | None = None

        self._window_session: WindowSession | None = None
        self._idle_session: IdleSession | None = None
        self._current_window_data: WindowData | None = None  # данные текущего окна, полученные из трекера

        self._autorefresh_statistics_task: asyncio.Task | None = None

    @property
    def is_activity_tracker_enabled(self) -> bool:
        return self._store.get('is_activity_tracker_enabled')

    @property
    def tracker(self) -> ActivityTracker:
        return self._store.get('activity_tracker')

    @property
    def opened_windows_component(self) -> OpenedWindowsComponent:
        return self._store.get('OpenedWindowsComponent')

    @property
    def activity_statistics_component(self) -> ActivityStatisticsView:
        return self._store.get('ActivityStatisticsView')

    def build(self):
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
        self.rebuild_tracking_status_text()
        self.window_session_ctrl = ft.Column(visible=False)
        self.idle_session_ctrl = ft.Column(visible=False)

        self._main_row = ft.Row(
            controls=[
                self._start_button,
                self._stop_button,
                self._tracking_status,
            ]
        )

        self.controls = [
            self._main_row,
            self.window_session_ctrl,
            self.idle_session_ctrl,
        ]

        super().build()

    async def start_resting(self, show_popup=True) -> None:
        if show_popup:
            NotificationSender().send_info('Время отдохнуть')

        if self._total_time_component and self._total_time_component in self._main_row.controls:
            self._main_row.controls.remove(self._total_time_component)

        self._total_time_component = TotalTimeComponent(
            label_text='Отдыхайте: ',
            on_end=self.start_working(),
        )
        self._main_row.controls.append(self._total_time_component)

        self.update()

    async def start_working(self, show_popup=True) -> None:
        if show_popup:
            NotificationSender().send_info('Пора работать')

        if self._total_time_component and self._total_time_component in self._main_row.controls:
            self._main_row.controls.remove(self._total_time_component)

        self._total_time_component = TotalTimeComponent(
            label_text='Сосредоточьтесь: ',
            on_end=self.start_resting()
        )
        self._main_row.controls.append(self._total_time_component)

        self.update()

    def rebuild_tracking_status_text(self):
        title = self.get_status_title()
        if not self._tracking_status:
            self._tracking_status = ft.Text(
                value=title,
                size=FontSize.H5,
            )
        else:
            self._tracking_status.value = title

    def get_status_title(self):
        if self.is_activity_tracker_enabled:
            return 'Отслеживание активности...'
        else:
            return 'Отслеживание активности выключено'

    async def _on_click_start(self, e):
        await self.start_tracking()

    async def start_tracking(self):
        self._store.set('is_activity_tracker_enabled', True)

        if self.opened_windows_component.is_active_windows_showed:
            # Уже есть данные о текущем открытом окне, записываем информацию в БД
            if self._current_window_data:
                self.switch_window_session(self._current_window_data, datetime.datetime.now(datetime.UTC))
        else:
            await self.tracker.start()

        await self._toggle_affected_on_start_stop()

    async def stop_tracking(self, ts: datetime.datetime = datetime.datetime.now(datetime.UTC)):
        self.stop_window_session(ts)
        self.stop_idle_session(ts)
        self._store.set('is_activity_tracker_enabled', False)
        await self._toggle_affected_on_start_stop()

    async def _on_click_stop(self, e):
        if self.opened_windows_component.is_active_windows_showed:
            await self.stop_tracking()
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
            self.activity_statistics_component.toggle_show_statistics(force_show=True)

            await self.start_working(show_popup=False)

            self._autorefresh_statistics_task = asyncio.create_task(self._run_auto_refresh_statistics())
        else:
            if self._total_time_component and self._total_time_component in self._main_row.controls:
                self._main_row.controls.remove(self._total_time_component)

            if self._autorefresh_statistics_task:
                await self._autorefresh_statistics_task

        self.update()

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

        self._store.set('window_session', self._window_session)

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

    def stop_window_session(self, ts: datetime.datetime):
        if not self.is_activity_tracker_enabled:
            return

        if self._window_session:
            self._window_session.stop(ts)

        self._window_session = None
        self._store.remove('window_session')
        self.window_session_ctrl.controls.clear()
        self.window_session_ctrl.update()

    def create_idle_session(self, ts: datetime.datetime):
        if not self.is_activity_tracker_enabled:
            return

        self._idle_session = IdleSession.create(start_ts=ts)
        self._store.set('idle_session', self._idle_session)
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

    # TODO: большая нагрузка при рефреше статистики: каждую секунду перезапрос в БД и отрисовка.
    #  Пока некритично
    async def _run_auto_refresh_statistics(self):
        while self.is_activity_tracker_enabled:
            self.activity_statistics_component.refresh_statistics()
            await asyncio.sleep(1)
