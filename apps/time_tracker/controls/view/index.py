import flet as ft

from apps.time_tracker.controls.statistics.index import ActivityStatisticsView
from apps.time_tracker.controls.view.opened_windows import OpenedWindowsComponent
from apps.time_tracker.controls.view.time_tracking import TimeTrackingComponent
from core.di import container


class ActivityTabViewControl(ft.Container):
    """Таб активности"""

    parent: ft.Tab
    content: ft.Row

    def __init__(self, **kwargs):
        kwargs.setdefault('padding', 20)
        super().__init__(**kwargs)

        self._store = container.session_store
        self._app_settings = container.app_settings

        self._time_tracking_component: TimeTrackingComponent | None = None
        self._opened_windows_component: OpenedWindowsComponent | None = None
        self._statistics_view: ActivityStatisticsView | None = None

    def build(self):
        self._time_tracking_component = TimeTrackingComponent()
        self._opened_windows_component = OpenedWindowsComponent()

        time_tracking_column = ft.Column(
            width=600,
            controls=[
                self._time_tracking_component,
                ft.Divider(),
                self._opened_windows_component,
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
