import flet as ft

from apps.time_tracker.models import IdleSession, WindowSession
from apps.time_tracker.services.window_control.abstract import WindowData
from apps.time_tracker.utils import get_app_name_and_transform_window_title
from core.di import container
from core.system_events.types import SystemEventSwitchWindowData, SystemEventTimestampData
from ui.components.timer import TimerComponent
from ui.consts import Colors


class CurrentWindowComponent(ft.Column):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._store = container.session_store
        self._app_settings = container.app_settings
        self._event_bus = container.event_bus

        self._event_bus.subscribe('window_tracker.switch_window', self.switch_window_session)
        self._event_bus.subscribe('activity_tracker.start', self.on_start_time_tracking)
        self._event_bus.subscribe('activity_tracker.detect_idle', self.create_idle_session)
        self._event_bus.subscribe('activity_tracker.stop', self.stop_idle_session)
        self._event_bus.subscribe('activity_tracker.stop_idle', self.stop_idle_session)
        self._event_bus.subscribe('activity_tracker.stop', self.stop_window_session)

        self._window_session: WindowSession | None = None
        self._idle_session: IdleSession | None = None
        self._current_window_data: WindowData | None = None  # данные текущего окна, полученные из трекера

    @property
    def is_window_tracker_enabled(self) -> bool:
        return self._store.get('is_window_tracker_enabled')

    def on_start_time_tracking(self, data: SystemEventTimestampData):
        # Если уже есть данные о текущем открытом окне, обновляем данные в интерфейсе и в БД
        if self._current_window_data:
            self.switch_window_session(
                SystemEventSwitchWindowData(
                    window=self._current_window_data,
                    ts=data.ts,
                )
            )

    def switch_window_session(self, data: SystemEventSwitchWindowData):
        window = data.window
        ts = data.ts

        self._current_window_data = window
        if not self.is_window_tracker_enabled:
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
        self._idle_session = None

        self._store.set('window_session', self._window_session)
        self._store.remove('idle_session')

        self.controls.clear()

        app_title = self._window_session.app_name
        if self._window_session.window_title:
            app_title += f' ({self._window_session.window_title})'

        self.controls.extend([
            TimerComponent(),
            ft.Text(
                value=app_title,
            )
        ])
        self.update()

    def create_idle_session(self, data: SystemEventTimestampData):
        if not self.is_window_tracker_enabled:
            return

        self._idle_session = IdleSession.create(start_ts=data.ts)
        self._store.set('idle_session', self._idle_session)

        self.controls.clear()
        self.controls.extend([
            TimerComponent(),
            ft.Text(
                value='Бездействие',
                color=Colors.RED_LIGHT,
            )
        ])
        self.update()

    def stop_window_session(self, data: SystemEventTimestampData):
        if not self.is_window_tracker_enabled:
            return

        if self._window_session:
            self._window_session.stop(data.ts)

        self._window_session = None
        self._store.remove('window_session')
        self.controls.clear()
        self.update()

    def stop_idle_session(self, data: SystemEventTimestampData):
        if not self.is_window_tracker_enabled:
            return

        if self._idle_session:
            self._idle_session.stop(data.ts)

        self._idle_session = None
        self._store.remove('idle_session')
        self.controls.clear()
        self.update()
