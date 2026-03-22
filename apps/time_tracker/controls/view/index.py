import flet as ft

from apps.time_tracker.controls.statistics.index import ActivityStatisticsView
from apps.time_tracker.controls.view.opened_windows import OpenedWindowsComponent
from apps.time_tracker.controls.view.time_tracking import TimeTrackingComponent
from apps.time_tracker.services.activity_tracker import ActivityTracker
from core.di import container
from ui.base.components.session_stored_component import SessionStoredComponent


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

        self.tracker: ActivityTracker | None = None

    @property
    def is_activity_tracker_enabled(self) -> bool:
        return self._store.get_or_create('is_activity_tracker_enabled', False)

    def build(self):
        self.tracker = ActivityTracker()
        self._store.set('activity_tracker', self.tracker)

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
