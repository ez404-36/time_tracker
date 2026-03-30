import flet as ft

from apps.time_tracker.services.window_tracker import WindowTracker
from apps.time_tracker.utils import get_app_name_and_transform_window_title
from core.di import container
from core.mixins import SessionStoredComponent
from core.system_events.types import SystemEventChangeActiveWindowsData
from ui.base.components.containers import BorderedContainer
from ui.consts import FontSize, FontWeight, Icons


class OpenedWindowsComponent(ft.Column, SessionStoredComponent):
    """
    Отображает текущие открытые окна
    """

    parent: ft.Container

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._store = container.session_store
        self._event_bus = container.event_bus

        self._show_opened_windows: ft.Checkbox | None = None
        self._opened_windows_text: ft.Text | None = None
        self.all_window_sessions_wrap: ft.Container | None = None
        self.all_window_sessions: ft.ListView | None = None

        self._event_bus.subscribe('tracker.change_opened_windows', self.update_all_active_window_sessions)

    def build(self):
        self.build_show_opened_windows_checkbox()
        self._opened_windows_text = ft.Text('Открытые окна', visible=False, size=FontSize.H5, weight=FontWeight.W_400)

        self.all_window_sessions = ft.ListView(
            expand=True,
        )

        self.all_window_sessions_wrap = BorderedContainer(
            content=self.all_window_sessions,
            padding=10,
            visible=False,
        )

        self.controls = [
            self._show_opened_windows,
            self._opened_windows_text,
            self.all_window_sessions_wrap,
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
        self.all_window_sessions_wrap.visible = value

        if not self._store.get('is_window_tracker_enabled'):
            # Если отслеживание активности не включено, включим трекер вручную
            tracker: WindowTracker = self._store.get('window_tracker')

            if value:
                await tracker.start()
            else:
                await tracker.stop()

        self.update()

    def update_all_active_window_sessions(self, data: SystemEventChangeActiveWindowsData):
        active_windows = data.active_windows

        self._opened_windows_text.value = f'Открытые окна ({len(active_windows)})'
        all_windows_component = self.all_window_sessions
        all_windows_component.controls.clear()

        for active_window in active_windows:
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

            row = ft.Row(
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

            all_windows_component.controls.append(row)

        self.update()
