import flet as ft

from ui.consts import FontSize


class OpenedWindowsComponent(ft.Column):
    parent: ft.Container

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._show_opened_windows: ft.Checkbox | None = None
        self._opened_windows_text: ft.Text | None = None
        self.all_window_sessions: ft.ListView | None = None

        self._is_active_windows_showed = False

    def build(self):
        self.build_show_opened_windows_checkbox()
        self._opened_windows_text = ft.Text('Открытые окна', visible=False, size=FontSize.H5, weight=ft.FontWeight.W_400)

        self.all_window_sessions = ft.ListView(
            expand=True,
        )

    def build_show_opened_windows_checkbox(self):
        self._show_opened_windows = ft.Checkbox(
            label='Показать открытые окна',
            on_change=self.on_click_show_opened_windows,
        )

    async def on_click_show_opened_windows(self, e):
        value: bool = e.control.value
        self._is_active_windows_showed = value

        self._opened_windows_text.visible = value
        self.all_window_sessions.visible = value

        if not self.parent._is_activity_tracker_enabled:
            # Если отслеживание активности не включено, включим трекер вручную
            if value:
                await self.tracker.start()
            else:
                await self.tracker.stop()

        self.update()