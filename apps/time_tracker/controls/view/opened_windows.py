import flet as ft

from apps.time_tracker.services.main_tracker import MainTracker
from apps.time_tracker.services.window_control.abstract import WindowData
from apps.time_tracker.utils import get_app_name_and_transform_window_title
from core.di import container
from core.mixins import SessionStoredComponent
from core.system_events.event_bus import EventBus
from core.system_events.types import SystemEventChangeActiveWindowsData, SystemEventChangeSettingsData
from ui.base.components.containers import BorderedContainer
from ui.base.components.mixins import ShowHideMixin
from ui.consts import FontSize, FontWeight, Icons


class OpenedWindowsComponent(
    ft.Column,
    SessionStoredComponent,
    ShowHideMixin,
):
    """
    Отображает текущие открытые окна
    """

    parent: ft.Container

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._store = container.session_store
        self._app_settings = container.app_settings
        self._event_bus: EventBus = container.event_bus
        self._main_tracker: MainTracker = container.main_tracker

        self._show_opened_windows: ft.Checkbox | None = None
        self._opened_windows_text: ft.Text | None = None
        self._all_window_sessions_wrap: ft.Container | None = None
        self._all_window_sessions: ft.ListView | None = None

        self.visible = self._app_settings.enable_window_tracking

        self._event_bus.subscribe('window_tracker.change_opened_windows', self.update_all_active_window_sessions)
        self._event_bus.subscribe('app.change_settings', self.on_event_change_settings)

    def build(self):
        self.build_show_opened_windows_checkbox()
        self._opened_windows_text = ft.Text('Открытые окна', visible=False, size=FontSize.H5, weight=FontWeight.W_400)

        self._all_window_sessions = ft.ListView(
            expand=True,
        )

        self._all_window_sessions_wrap = BorderedContainer(
            content=self._all_window_sessions,
            padding=10,
            visible=False,
        )

        self.controls = [
            self._show_opened_windows,
            self._opened_windows_text,
            self._all_window_sessions_wrap,
        ]
        super().build()

    def build_show_opened_windows_checkbox(self):
        self._show_opened_windows = ft.Checkbox(
            label='Показать открытые окна',
            on_change=self.on_click_show_opened_windows,
        )

    async def on_click_show_opened_windows(self, e):
        value: bool = e.control.value

        self._opened_windows_text.visible = value
        self._all_window_sessions_wrap.visible = value

        main_tracker = self._main_tracker

        if not main_tracker.running:
            # Если глобальное отслеживание активности не включено, включим трекер окон вручную
            if value:
                await main_tracker.window_tracker.start()
            else:
                await main_tracker.window_tracker.stop()

        self.update()

    def on_event_change_settings(self, data: SystemEventChangeSettingsData):
        tracker_settings = data.values['tracker']
        enable_window_tracking = tracker_settings.get('enable_window_tracking', self._app_settings.enable_window_tracking)

        self.visible = enable_window_tracking

        self.update()

    def update_all_active_window_sessions(self, data: SystemEventChangeActiveWindowsData):
        active_windows = data.active_windows

        self._opened_windows_text.value = f'Открытые окна ({len(active_windows)})'
        all_windows_component = self._all_window_sessions
        all_windows_component.controls.clear()

        for active_window in active_windows:
            row = self._build_active_window_row(active_window)
            all_windows_component.controls.append(row)

        self.update()

    @staticmethod
    def _build_active_window_row(active_window: WindowData) -> ft.Row:
        app_name, window_title = get_app_name_and_transform_window_title(
            active_window['executable_name'],
            active_window['window_title']
        )
        title = app_name
        if window_title:
            app_name += f' ({window_title})'

        executable_title = active_window['executable_name']
        if active_window['executable_path']:
            executable_title += f' ({active_window['executable_path']}'

        return ft.Row(
            controls=[
                ft.Icon(Icons.APPS),
                ft.Text(
                    value=title,
                    tooltip=ft.Tooltip(
                        message=executable_title,
                        # TODO: тултип мигает
                    ),
                )
            ]
        )
