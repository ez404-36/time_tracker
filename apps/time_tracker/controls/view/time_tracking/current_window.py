import flet as ft

from apps.time_tracker.models import IdleSession, WindowSession
from apps.time_tracker.services.window_control.abstract import WindowData
from apps.time_tracker.utils import get_app_name_and_transform_window_title
from core.di import container
from core.mixins.tracker_info_mixin import TrackerInfoMixin
from core.system_events.types import SystemEventSwitchWindowData, SystemEventTimestampData, SystemEventStartMainTracker
from ui.base.components.containers import BorderedContainer
from ui.base.components.mixins import ShowHideMixin
from ui.components.timer import TimerComponent
from ui.consts import Colors, FontSize


class CurrentWindowComponent(
    BorderedContainer,
    ShowHideMixin,
    TrackerInfoMixin,
):
    content: ft.Column

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._store = container.session_store
        self._app_settings = container.app_settings
        self._event_bus = container.event_bus

        self._window_session: WindowSession | None = None
        self._idle_session: IdleSession | None = None
        self._current_window_data: WindowData | None = None  # данные текущего окна, полученные из трекера

        self.content = ft.Column()

        self._event_bus.subscribe('window_tracker.switch_window', self.switch_window_session)
        self._event_bus.subscribe('main_tracker.start', self.on_start_main_tracker)
        self._event_bus.subscribe('main_tracker.pause', self.hide)
        self._event_bus.subscribe('main_tracker.resume', self.show)
        self._event_bus.subscribe('main_tracker.stop', self.on_stop_main_tracker)
        self._event_bus.subscribe('activity_tracker.detect_idle', self.on_detect_idle)
        self._event_bus.subscribe('activity_tracker.stop_idle', self.stop_idle_session)

    def on_start_main_tracker(self, data: SystemEventStartMainTracker):
        self._set_tracker_config_on_start(data)

        if data.window_tracking:
            # Если уже есть данные о текущем открытом окне, обновляем данные в интерфейсе и в БД
            if self._current_window_data:
                self.switch_window_session(
                    SystemEventSwitchWindowData(
                        window=self._current_window_data,
                    )
                )
            else:
                self.switch_window_session(
                    SystemEventSwitchWindowData(
                        window={
                            'executable_name': 'Нет данных',
                            'window_title': None,
                            'executable_path': None,
                        }
                    )
                )

            self.show()

    def on_stop_main_tracker(self, data: SystemEventTimestampData):
        self._set_tracker_config_on_stop()

        self.stop_window_session(data)
        self.stop_idle_session(data)
        self._rebuild_component(
            top_label_text=None,
            timer=None,
            main_label_text=None,
            bg_color=Colors.WHITE,
        )
        self.hide()

    def switch_window_session(self, data: SystemEventSwitchWindowData):
        window = data.window
        ts = data.ts

        self._current_window_data = window

        if not self._is_tracker_running or not self._tracker_config.window_tracking:
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

        app_title = self._window_session.app_name
        if self._window_session.window_title:
            app_title += f' ({self._window_session.window_title})'

        self._rebuild_component(
            top_label_text='Активное окно',
            timer=TimerComponent(),
            main_label_text=app_title,
            bg_color=Colors.WHITE,
        )

    def on_detect_idle(self, data: SystemEventTimestampData):
        if not self._is_tracker_running or not self._tracker_config.idle_tracking:
            return

        self._idle_session = IdleSession.create(start_ts=data.ts)
        self._store.set('idle_session', self._idle_session)

        self._rebuild_component(
            top_label_text=None,
            timer=TimerComponent(),
            main_label_text='Бездействие',
            bg_color=Colors.RED_LIGHT,
        )

    def stop_window_session(self, data: SystemEventTimestampData):
        if not self._is_tracker_running or not self._tracker_config.window_tracking:
            return

        if self._window_session:
            self._window_session.stop(data.ts)

        self._window_session = None
        self._store.remove('window_session')
        self._reset()
        self.update()

    def stop_idle_session(self, data: SystemEventTimestampData):
        if not self._is_tracker_running or not self._tracker_config.idle_tracking:
            return

        if self._idle_session:
            self._idle_session.stop(data.ts)

        self._idle_session = None
        self._store.remove('idle_session')

    def _rebuild_component(
            self,
            top_label_text: str | None,
            timer: TimerComponent | None,
            main_label_text: str | None,
            bg_color: ft.Colors | None,
    ):
        self._reset()

        top_row_controls = []
        if top_label_text:
            top_row_controls.append(
                ft.Text(
                    value=top_label_text,
                    size=FontSize.REGULAR,
                )
            )

        if timer:
            top_row_controls.append(timer)

        if top_row_controls:
            self.content.controls.append(
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=top_row_controls,
                )
            )

        if main_label_text:
            self.content.controls.append(
                ft.Row(
                    alignment=ft.MainAxisAlignment.CENTER,
                    controls=[
                        ft.Text(
                            value=main_label_text,
                            size=FontSize.H4,
                            tooltip=main_label_text if len(main_label_text) > 20 else None,
                        )
                    ],
                )

            )

        if bg_color:
            self.bgcolor = bg_color

        self.update()

    def _reset(self):
        self.content.controls.clear()
