import flet as ft

from apps.time_tracker.controls.statistics.index import ActivityStatisticsView
from apps.time_tracker.controls.view.opened_windows import OpenedWindowsComponent
from apps.time_tracker.controls.view.time_tracking import TimeTrackingComponent
from apps.time_tracker.services.window_tracker import WindowTracker
from core.di import container
from core.mixins import SessionStoredComponent


class ActivityTabViewControl(ft.Container, SessionStoredComponent):
    """Таб активности"""

    parent: ft.Tab
    content: ft.Row

    def __init__(self, **kwargs):
        kwargs.setdefault('padding', 20)
        super().__init__(**kwargs)
        self._store = container.session_store
        self._app_settings = container.app_settings

        self.time_tracking_component: TimeTrackingComponent | None = None
        self.opened_windows_component: OpenedWindowsComponent | None = None
        self._statistics_view: ActivityStatisticsView | None = None

        self.tracker: WindowTracker | None = None

    @property
    def is_window_tracker_enabled(self) -> bool:
        return self._store.get_or_create('is_window_tracker_enabled', False)

    def build(self):
        self.tracker = WindowTracker()
        self._store.set('window_tracker', self.tracker)

        self.time_tracking_component = TimeTrackingComponent()
        self.opened_windows_component = OpenedWindowsComponent()

        time_tracking_column = ft.Column(
            width=600,
            controls=[
                self.time_tracking_component,
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
