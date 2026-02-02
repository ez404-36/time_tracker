from typing import Any, TypedDict

import flet as ft

from apps.time_tracker.controls.view.statistics.one_row import StatisticsOneRow
from apps.time_tracker.controls.view.statistics.sort_dropdown import StatisticsSortDropdown


class WindowTitleSessionData(TypedDict):
    window_title: str
    duration: int


class OneAppView(ft.Column):
    """
    Компонент отображения статистики по одному приложению
    """

    def __init__(
            self,
            app_name: str,
            total_time: int,
            sessions: list[WindowTitleSessionData] | None = None,
            **kwargs,
    ):
        super().__init__(**kwargs)
        self._app_name = app_name
        self._sessions = sessions
        self._total_time = total_time

        self._sort_component: StatisticsSortDropdown | None = None
        self._main_row: StatisticsOneRow | None = None

    def build(self):
        self._sort_component = StatisticsSortDropdown(text_size=12)
        self._main_row = StatisticsOneRow(self._app_name, self._total_time, False, bool(self._sessions))

        controls: list[Any] = [
            ft.Row(
                controls=[
                    self._main_row,
                    # self._sort_component,
                ]
            ),
        ]

        if self._sessions:
            for session in self._sessions:
                controls.append(
                    StatisticsOneRow(session['window_title'], session['duration'], True, False)
                )

        self.controls = controls
